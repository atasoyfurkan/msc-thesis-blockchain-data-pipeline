import os
import requests
from requests.exceptions import HTTPError
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO
from typing import Optional

class DataPipelineClient:
    """
    A client for interacting with the Data Pipeline API.
    This client handles querying data and retrieving parquet files.
    """

    def __init__(self):
        """
        Initialize the client with the base URL of the API.
        :param base_url: The base URL of the FastAPI server (e.g., 'http://localhost:8000')
        """
        self.base_url = os.getenv("PIPELINE_API_BACKEND_URL")
        self.token = os.getenv("JUPYTERHUB_API_TOKEN")

        if not self.token or not self.base_url:
            raise ValueError("JUPYTERHUB_API_TOKEN or PIPELINE_API_BACKEND_URL environment variable is not set")
    
    def _get_auth_headers(self) -> dict:
        """Get the authorization headers for API requests."""
        return {"Authorization": f"token {self.token}"}

    def list_buckets(self) -> list[str]:
        """Fetch the list of all buckets."""
        response = requests.get(f"{self.base_url}/buckets", headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()

    def list_files(self, bucket_name: str) -> list[dict]:
        """Fetch the list of files in a given bucket."""
        response = requests.get(f"{self.base_url}/files/{bucket_name}", headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()

    def list_dates(self, bucket_name: str) -> list[str]:
        """Fetch the available dates for a given bucket."""
        response = requests.get(f"{self.base_url}/dates/{bucket_name}", headers=self._get_auth_headers())
        response.raise_for_status()
        return response.json()

    def get_table_path(self, bucket_name: str, start_date: str = None, end_date: str = None, dates: str = None) -> str:
        """
        Fetch table paths based on a date range or specific dates.
        :param bucket_name: Name of the bucket
        :param start_date: Start date in 'YYYY/MM/DD' format (optional)
        :param end_date: End date in 'YYYY/MM/DD' format (optional)
        :param dates: List of specific dates in 'YYYY/MM/DD' format (optional)
        """
        params = {}
        if dates:
            params['dates'] = dates
        elif start_date and end_date:
            params['start_date'] = start_date
            params['end_date'] = end_date
        else:
            raise ValueError("Either 'dates' or 'start_date' and 'end_date' must be provided")

        try:
            response = requests.get(f"{self.base_url}/table_path/{bucket_name}", params=params, headers=self._get_auth_headers())
            response.raise_for_status()

            return response.json()
        except HTTPError as exception:
            if exception.response.status_code == 400:
                raise ValueError(f"Invalid request (400): {response.text}")
            else:
                raise HTTPError(f"Failed to fetch table path {response.text}")

    def execute_query(self, query: str, persist: bool = False, custom_username: Optional[str] = None) -> pd.DataFrame:
        """
        Execute a query on DuckDB and return the result as a pandas DataFrame.
        :param 
            query: The SQL query to execute
            persist: Whether to persist the query results (after retention period, the data will be automatically deleted)
            custom_username: The custom username to use for the persistent queries instead of the current user (only admins can use this)
        :return: pandas DataFrame containing the query result.
        """
        try:
            params = {'query': query, 'persist': persist}
            if custom_username:
                params['custom_username'] = custom_username

            response = requests.get(f"{self.base_url}/execute_query", params=params, headers=self._get_auth_headers())
            response.raise_for_status()

            # Read the parquet data into a DataFrame
            parquet_data = BytesIO(response.content)
            return pq.read_table(parquet_data).to_pandas()
        except HTTPError as exception:
            if exception.response.status_code == 500:
                raise HTTPError(f"Internal Server Error (500): Failed to execute query {response.text}")
            if exception.response.status_code == 504:
                raise HTTPError(f"Gateway Timeout (504): Query execution timed out {response.text}. Please run a smaller query.")
            else:
                raise HTTPError(f"Failed to execute query {response.text}")
    
    def list_persistent_queries(self, custom_username: Optional[str] = None) -> pd.DataFrame:
        """
        List all the persistent queries metadata for the current user.
        :param custom_username: The custom username to use for the persistent queries instead of the current user (only admins can use this)
        """
        try:
            params = {}
            if custom_username:
                params['custom_username'] = custom_username
            
            response = requests.get(f"{self.base_url}/persistent_query/metadata", params=params, headers=self._get_auth_headers())
            response.raise_for_status()

            parquet_data = BytesIO(response.content)
            return pq.read_table(parquet_data).to_pandas()
        except HTTPError as exception:
            if exception.response.status_code == 500:
                raise HTTPError(f"Internal Server Error (500): Failed to list persisted queries {response.text}")
            else:
                raise HTTPError(f"Failed to list persisted queries {response.text}")
    
    def fetch_persistent_query(self, query: str, custom_username: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch the persisted query result for a given query_id.
        :param query: The query to fetch.
        :param custom_username: The custom username to use for the persistent queries instead of the current user (only admins can use this)
        """
        try:
            params = {'query': query}
            if custom_username:
                params['custom_username'] = custom_username

            response = requests.get(f"{self.base_url}/persistent_query/data", params=params, headers=self._get_auth_headers())
            response.raise_for_status()

            parquet_data = BytesIO(response.content)
            return pq.read_table(parquet_data).to_pandas()
        except HTTPError as exception:
            if exception.response.status_code == 500:
                raise HTTPError(f"Internal Server Error (500): Failed to fetch persisted query {response.text}")
            else:
                raise HTTPError(f"Failed to fetch persisted query {response.text}")