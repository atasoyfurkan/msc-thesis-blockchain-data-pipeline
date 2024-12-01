# Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN pip install pandas pyarrow requests minio

WORKDIR /app
# copy other modules
COPY ../.. .
# copy main.py
COPY services/price_data_fetcher/main.py .

# set root directory
ENV PYTHONPATH=/app

# Command to run the script
CMD ["python", "main.py"]