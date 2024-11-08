# Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN pip install websocket-client pandas pyarrow requests minio

# Copy the script
WORKDIR /app
COPY . .

# Command to run the script
CMD ["python", "main.py"]