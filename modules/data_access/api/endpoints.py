from modules.data_access.duckdb.manager import DuckDBManager
from modules.data_access.cache.persistent_query_manager import PersistentQueryManager
from modules.data_storage.minio.read_client import MinioReadClient
from modules.data_storage.minio.write_client import MinioWriteClient
from modules.data_access.api.auth import authenticate_user
import os
from io import BytesIO
from typing import Optional
import logging
import time
from fastapi import APIRouter, HTTPException, Response, Query, Depends
import pyarrow as pa
import pyarrow.parquet as pq
from prometheus_client import Histogram

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

# Prometheus metrics
QUERY_LATENCY = Histogram('api_backend_query_latency_seconds', 'Time taken to execute DuckDB queries')

# Load environment variables
MINIO_DATALAKE_ENDPOINT = os.getenv("MINIO_DATALAKE_ENDPOINT")
MINIO_CACHE_ENDPOINT = os.getenv("MINIO_CACHE_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

QUERY_TIMEOUT_SECONDS = float(os.getenv("QUERY_TIMEOUT_SECONDS"))
PERSISTENT_QUERY_RETENTION_DAYS = int(os.getenv("PERSISTENT_QUERY_RETENTION_DAYS")) # Number of days to retain the persistent query results

if not MINIO_DATALAKE_ENDPOINT or not MINIO_CACHE_ENDPOINT or not MINIO_ROOT_USER or not MINIO_ROOT_PASSWORD or not QUERY_TIMEOUT_SECONDS:
    raise ValueError("Missing required environment variables")

# Initialize clients
minio_client = MinioReadClient(
    endpoint=MINIO_DATALAKE_ENDPOINT,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD
)
duckdb_manager = DuckDBManager(minio_read_client=minio_client)

minio_cache_write_client = MinioWriteClient(
    endpoint=MINIO_CACHE_ENDPOINT,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD
)
persistent_query_manager = PersistentQueryManager(
    minio_write_client=minio_cache_write_client, 
    retention_days=PERSISTENT_QUERY_RETENTION_DAYS,
    duckdb_manager=duckdb_manager
)

router = APIRouter()

@router.get("/buckets")
def list_buckets(user = Depends(authenticate_user)):
    return minio_client.list_buckets()

@router.get("/files/{bucket_name}")
def list_files(bucket_name: str, user = Depends(authenticate_user)):
    return minio_client.list_objects(bucket_name=bucket_name)

@router.get("/dates/{bucket_name}")
def list_dates(bucket_name: str, user = Depends(authenticate_user)):
    return minio_client.list_dates(bucket_name=bucket_name)

@router.get("/table_path/{bucket_name}")
def get_table_path(
    bucket_name: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    dates: Optional[list[str]] = Query(None),
    user = Depends(authenticate_user)
):
    if not (dates or (start_date and end_date)):
        raise HTTPException(status_code=400, detail="Either 'dates' or 'start_date' and 'end_date' must be provided")    
    # In the future, we can add validation for date format to check if it is correctly provided

    try:
        if dates:
            table_path = duckdb_manager.get_table_path_with_dates(bucket_name=bucket_name, dates=dates)
        else:
            table_path = duckdb_manager.get_table_path_with_range(bucket_name=bucket_name, start_date=start_date, end_date=end_date)
        
        return table_path
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate table path: {e}")

def _convert_df_to_parquet(df) -> BytesIO:
    """Convert a DataFrame to Parquet in-memory."""
    table = pa.Table.from_pandas(df)
    output = BytesIO()
    pq.write_table(table, output, compression='snappy')
    output.seek(0)
    return output

def _get_parquet_response_headers():
    return {
        "Content-Disposition": "attachment; filename=result.parquet",
        "Content-Type": "application/vnd.apache.parquet"
    }

@router.get("/execute_query")
def execute_query_duckdb(query: str, persist: bool, custom_username: Optional[str] = None, user = Depends(authenticate_user)):
    """
    Execute a query on DuckDB and return compressed Parquet data.
    Args:
        query: The SQL query to execute.
        persist: Whether to persist the query results.
        custom_username: The custom username to use for the persistent queries (only admin can use this)
    """
    start_time = time.time()

    try:
        # Query DuckDB
        result_df = duckdb_manager.execute_query_with_timeout(query, timeout=QUERY_TIMEOUT_SECONDS)
        logging.debug(f"Query result: {result_df}")

        if persist:
            username = custom_username if user["admin"] and custom_username else user["name"]
            persistent_query_manager.persist(df=result_df, query=query, username=username)
        
        # Convert DataFrame to Parquet
        output = _convert_df_to_parquet(result_df)

        logging.debug(f"Query latency: {time.time() - start_time}")
        QUERY_LATENCY.observe(time.time() - start_time)
        return Response(content=output.read(), headers=_get_parquet_response_headers())
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=f"Query execution timed out and was cancelled: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")
    
@router.get("/persistent_query/metadata")
def list_persistent_queries(custom_username: Optional[str] = None, user = Depends(authenticate_user)):
    """
    List all the persisted queries metadata for the user.
    Args:
        custom_username: The custom username to use for the persistent queries (only admin can use this)
    """
    try:
        username = custom_username if user["admin"] and custom_username else user["name"]
        metadata_df = persistent_query_manager.list_metadata(username=username)

        return Response(content=_convert_df_to_parquet(metadata_df).read(), headers=_get_parquet_response_headers())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list persisted queries: {e}")
    
@router.get("/persistent_query/data")
def fetch_persistent_query(query: str, custom_username: Optional[str] = None, user = Depends(authenticate_user)):
    """
    Fetch the persisted query result for given query from MinIO.
    Args:
        query: The query to fetch.
        custom_username: The custom username to use for the persistent queries (only admin can use this)
    """
    start_time = time.time()

    try:
        username = custom_username if user["admin"] and custom_username else user["name"]
        result_df = persistent_query_manager.fetch_data(username=username, query=query)

        output = _convert_df_to_parquet(result_df)

        logging.debug(f"Query latency: {time.time() - start_time}")
        QUERY_LATENCY.observe(time.time() - start_time)
        return Response(content=output.read(), headers=_get_parquet_response_headers())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch persisted query data: {e}")