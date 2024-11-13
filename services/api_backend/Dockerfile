# Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN pip install minio duckdb pandas fastapi uvicorn pyarrow requests

WORKDIR /app
# copy other modules
COPY ../.. .
# copy main.py
COPY services/api_backend/main.py .

# set root directory
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Command to run the script
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]