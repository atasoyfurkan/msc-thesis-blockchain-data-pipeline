# Stage 1: Build Python Dependencies
FROM python:3.9-slim as build

WORKDIR /app
RUN pip install minio duckdb pandas fastapi uvicorn pyarrow requests prometheus_client

# Stage 2: Final Image
FROM python:3.9-slim

# Copy installed dependencies from the build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

WORKDIR /app
# Copy application code
COPY modules modules
COPY services/api_backend/main.py main.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
