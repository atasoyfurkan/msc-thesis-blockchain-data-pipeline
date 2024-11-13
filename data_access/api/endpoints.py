from data_access.duckdb.manager import DuckDBManager
from data_storage.minio.read_client import MinioReadClient
from data_access.api.auth import authenticate_user
import os
from io import BytesIO
from typing import Optional
import logging
from fastapi import APIRouter, HTTPException, Response, Query, Depends
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load environment variables
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")

# Initialize clients
minio_client = MinioReadClient(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD
)
duckdb_manager = DuckDBManager(minio_read_client=minio_client)

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

@router.get("/tables/{bucket_name}")
def get_tables(
    bucket_name: str, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None, 
    dates: Optional[list[str]] = Query(None),
    user = Depends(authenticate_user)
):
    if not (dates or (start_date and end_date)):
        raise HTTPException(status_code=400, detail="Either 'dates' or 'start_date' and 'end_date' must be provided")

    try:
        if dates:
            tables = duckdb_manager.get_tables_with_dates(bucket_name=bucket_name, dates=dates)
        else:
            tables = duckdb_manager.get_tables_with_range(bucket_name=bucket_name, start_date=start_date, end_date=end_date)
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tables: {e}")

@router.get("/query")
def query_duckdb(query: str, user = Depends(authenticate_user)):
    """Execute a query on DuckDB and return compressed Parquet data."""
    try:
        # Query DuckDB
        result_df = duckdb_manager.query(query)
        
        # Convert DataFrame to Parquet in-memory
        table = pa.Table.from_pandas(result_df)
        output = BytesIO()
        pq.write_table(table, output, compression='snappy')
        output.seek(0)

        # Set headers for file download
        headers = {
            "Content-Disposition": "attachment; filename=result.parquet",
            "Content-Type": "application/vnd.apache.parquet"
        }

        return Response(content=output.read(), headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")