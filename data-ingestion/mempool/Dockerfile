# Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN pip install websocket-client pandas pyarrow requests

# Copy the script
WORKDIR /app
COPY fetch_mempool.py /app/fetch_mempool.py

# Set environment variable for data storage
ENV DATA_DIR /data/mempool
RUN mkdir -p $DATA_DIR

# Command to run the script
CMD ["python", "/app/fetch_mempool.py"]