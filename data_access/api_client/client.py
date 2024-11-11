import requests
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO

class DataPipelineClient:
    """
    A client for interacting with the Data Pipeline API.
    This client handles querying data and retrieving parquet files.
    """

    def __init__(self, base_url: str):
        """
        Initialize the client with the base URL of the API.
        :param base_url: The base URL of the FastAPI server (e.g., 'http://localhost:8000')
        """
        self.base_url = base_url.rstrip('/')

    def list_buckets(self) -> list[str]:
        """Fetch the list of all buckets."""
        response = requests.get(f"{self.base_url}/buckets")
        response.raise_for_status()
        return response.json()

    def list_files(self, bucket_name: str) -> list[dict]:
        """Fetch the list of files in a given bucket."""
        response = requests.get(f"{self.base_url}/files/{bucket_name}")
        response.raise_for_status()
        return response.json()

    def list_dates(self, bucket_name: str) -> list[str]:
        """Fetch the available dates for a given bucket."""
        response = requests.get(f"{self.base_url}/dates/{bucket_name}")
        response.raise_for_status()
        return response.json()

    def get_tables(self, bucket_name: str, start_date=None, end_date=None, dates=None) -> str:
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

        response = requests.get(f"{self.base_url}/tables/{bucket_name}", params=params)
        response.raise_for_status()
        return response.json()

    def query(self, query: str) -> pd.DataFrame:
        """
        Execute a query on DuckDB and return the result as a pandas DataFrame.
        :param query: The SQL query to execute.
        :return: pandas DataFrame containing the query result.
        """
        response = requests.get(f"{self.base_url}/query", params={'query': query})
        response.raise_for_status()

        # Read the parquet data into a DataFrame
        parquet_data = BytesIO(response.content)
        return pq.read_table(parquet_data).to_pandas()
