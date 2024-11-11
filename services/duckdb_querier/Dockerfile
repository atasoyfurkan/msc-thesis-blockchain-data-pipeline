# Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN pip install minio duckdb pandas

WORKDIR /app
# copy other modules
COPY ../.. .
# copy main.py
COPY services/duckdb_querier/main.py .

# set root directory
ENV PYTHONPATH=/app

# Command to run the script
CMD ["python", "main.py"]