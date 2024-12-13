# Stage 1: Build Python Dependencies
FROM python:3.9-slim as build

WORKDIR /app
RUN pip install requests pandas pyarrow

# Stage 2: Final Image
FROM python:3.9-slim


# Copy installed dependencies from the build stage
COPY --from=build /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=build /usr/local/bin /usr/local/bin

WORKDIR /app
# Copy application code
COPY modules modules
COPY services/api_client/main.py main.py

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "main.py"]