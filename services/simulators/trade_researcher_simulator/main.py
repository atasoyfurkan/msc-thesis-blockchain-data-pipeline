from modules.data_access.workload_simulator.workload_simulator import WorkloadSimulator
from modules.data_access.workload_simulator.trade_researcher_notebook import run_trade_researcher_notebook
import logging
import os
from distutils.util import strtobool

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    MEAN_INTERARRIVAL_TIME_SECONDS = int(os.getenv("MEAN_INTERARRIVAL_TIME_SECONDS"))
    UNIQUE_USERNAME = os.getenv("UNIQUE_USERNAME")
    PERSISTENT_QUERY_USAGE_PROBABILITY = float(os.getenv("PERSISTENT_QUERY_USAGE_PROBABILITY"))
    ENABLE_PERSISTENT_QUERY = bool(strtobool(os.getenv("ENABLE_PERSISTENT_QUERY")))

    if not MEAN_INTERARRIVAL_TIME_SECONDS:
        raise ValueError("Missing required environment variable")

    simulator = WorkloadSimulator(
        mean_interarrival_time_seconds=MEAN_INTERARRIVAL_TIME_SECONDS, 
        unique_username=UNIQUE_USERNAME, 
        notebook_runner=run_trade_researcher_notebook,
        persistent_query_usage_probability=PERSISTENT_QUERY_USAGE_PROBABILITY,
        enable_persistent_query=ENABLE_PERSISTENT_QUERY
    )
    simulator.run()

if __name__ == "__main__":
    main()
