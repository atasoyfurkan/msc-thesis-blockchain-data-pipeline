# Dockerfile

FROM python:3.9-slim

# Install dependencies
RUN pip install requests pandas pyarrow 

WORKDIR /app
# copy other modules
COPY ../.. .
# copy main.py
COPY services/api_client/main.py .

# set root directory
ENV PYTHONPATH=/app

# Command to run the script
CMD ["python", "main.py"]