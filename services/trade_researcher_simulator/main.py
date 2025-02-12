from modules.data_access.workload_simulator.trade_researcher_simulator import TradeResearcherWorkloadSimulator
import logging
import os

logging.basicConfig(level=os.getenv("LOGGING_LEVEL", "INFO"), format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    MEAN_INTERARRIVAL_TIME_SECONDS = int(os.getenv("MEAN_INTERARRIVAL_TIME_SECONDS"))

    if not MEAN_INTERARRIVAL_TIME_SECONDS:
        raise ValueError("Missing required environment variable")

    simulator = TradeResearcherWorkloadSimulator(mean_interarrival_time_seconds=MEAN_INTERARRIVAL_TIME_SECONDS)
    simulator.run()

if __name__ == "__main__":
    main()
