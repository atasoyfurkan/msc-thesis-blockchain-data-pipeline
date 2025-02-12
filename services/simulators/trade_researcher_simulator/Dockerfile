# Stage 1: Build Python Dependencies
FROM python:3.9-slim as build

WORKDIR /app
RUN pip install requests pandas pyarrow matplotlib seaborn 

# Stage 2: Final Image
FROM python:3.9-slim

# Copy installed dependencies from the build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

WORKDIR /app
# copy other modules
COPY modules modules
# copy main.py
COPY services/simulators/trade_researcher_simulator/main.py main.py

# set root directory
ENV PYTHONPATH=/app

# Command to run the script
CMD ["python", "main.py"]