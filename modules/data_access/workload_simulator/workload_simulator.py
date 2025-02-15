from modules.data_access.api_client.client import DataPipelineClient
from modules.data_access.cache.persistent_query_manager import PersistentQueryManager
from modules.data_access.workload_simulator.trade_researcher_notebook import run_trade_researcher_notebook
import logging
import random
import time
from typing import Callable, Optional

class WorkloadSimulator:
    """
    This class simulates the workloads for different personas.
    It runs the given notebook at exponentially distributed interarrival times.
    """
    def __init__(self, mean_interarrival_time_seconds: int, unique_username: str, notebook_runner: Callable, persistent_query_usage_probability: float):
        self.client = DataPipelineClientWithCachingProbability(
            persistent_query_usage_probability=persistent_query_usage_probability, 
            unique_username=unique_username
        )
        self.mean_interarrival_time_seconds = mean_interarrival_time_seconds
        self.unique_username = unique_username
        self.notebook_runner = notebook_runner

    def run(self):
        while True:
            # Sleep
            sleep_time = self._calculate_expontential_interarival_time()
            logging.info(f"Sleeping for {sleep_time} seconds before next notebook run...")
            time.sleep(sleep_time)

            # Run notebook
            start_index, end_index = self._generate_random_date_indices()
            logging.info(f"Running price impact analysis for date indices {start_index} to {end_index}")
            self.notebook_runner(self.client, start_index, end_index)


    def _calculate_expontential_interarival_time(self):
        return random.expovariate(1.0 / self.mean_interarrival_time_seconds)

    def _generate_random_date_indices(self):
        """
        Randomly get a date interval between the latest 15 days to run the simulation over it.
        """
        start_index = random.randint(-15, 0)  # Random start index between latest 15 days
        days_taken = random.randint(1, 2)  # Random duration between 1 to 5 days
        end_index = start_index + days_taken  # Ensure end index is at most 5 further than start

        return start_index, end_index

class DataPipelineClientWithCachingProbability(DataPipelineClient):
    def __init__(self, persistent_query_usage_probability: float, unique_username: str):
        super().__init__()
        self.persistent_query_usage_probability = persistent_query_usage_probability
        self.unique_username = unique_username

    def _is_query_already_persisted(self, query: str, custom_username: Optional[str] = None):
        """Check if the query is already persisted in the cache."""
        metadata_df = self.list_persistent_queries(custom_username=custom_username)
        query = PersistentQueryManager.clean_query(query)
        return query in metadata_df["query"].values

    def execute_query(self, query: str, persist: bool = False, custom_username: Optional[str] = None):
        if random.random() < self.persistent_query_usage_probability and self._is_query_already_persisted(query, self.unique_username):
            logging.info(f"Using persistent query for user: {self.unique_username} with probability {self.persistent_query_usage_probability}")
            super().fetch_persistent_query(query, custom_username=self.unique_username)
        else: # Do not use persistent queries
            return super().execute_query(query, persist=True, custom_username=self.unique_username)
