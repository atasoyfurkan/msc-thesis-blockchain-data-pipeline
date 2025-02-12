from modules.data_access.api_client.client import DataPipelineClient
from modules.data_access.workload_simulator.trade_researcher_notebook import run_trade_researcher_notebook
import logging
import random
import time
from typing import Callable

class WorkloadSimulator:
    """
    This class simulates the workloads for different personas.
    It runs the given notebook at exponentially distributed interarrival times.
    """

    def __init__(self, mean_interarrival_time_seconds: int, notebook_runner: Callable):
        self.client = DataPipelineClient()
        self.mean_interarrival_time_seconds = mean_interarrival_time_seconds
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
        start_index = random.randint(-15, 0)  # Random start index between latest 15 days
        days_taken = random.randint(1, 2)  # Random duration between 1 to 5 days
        end_index = start_index + days_taken  # Ensure end index is at most 5 further than start

        return start_index, end_index