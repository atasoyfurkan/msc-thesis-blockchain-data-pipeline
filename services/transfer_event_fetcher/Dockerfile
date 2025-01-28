# Stage 1: Build Python Dependencies
FROM python:3.9-slim as build

WORKDIR /app
RUN pip install websocket-client pandas pyarrow requests minio prometheus_client

# Stage 2: Final Image
FROM python:3.9-slim

# Copy installed dependencies from the build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

WORKDIR /app
# copy other modules
COPY modules modules
# copy main.py
COPY services/transfer_event_fetcher/main.py main.py
# copy token_configurations.json
COPY services/transfer_event_fetcher/token_configurations.json token_configurations.json

# set root directory
ENV PYTHONPATH=/app

# Command to run the script
CMD ["python", "main.py"]