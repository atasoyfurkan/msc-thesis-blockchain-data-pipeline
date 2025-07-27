# Building a Production-Ready Data Pipeline for Large-Scale Data Processing

This repository contains the codebase for a production-ready data pipeline developed for ingesting, processing, and serving large-scale blockchain data. It was implemented as part of a Master’s thesis at the Technical University of Munich.

## Overview

The pipeline supports real-time and batch ingestion, efficient querying, and access via JupyterHub. The main use case is Maximal Extractable Value (MEV) analysis, which involves analyzing blockchain transaction patterns, gas prices, and price impacts.

## Architecture

![Architecture Diagram](docs/architecture.png)

- **Data Sources**: On-chain data from a local Ethereum node (WebSocket) and off-chain price data from Binance API (REST).
- **Ingestion Layer**: Block, transfer event, mempool, and price data fetchers write raw data to MinIO (data lake) via S3 API.
- **Storage**: Data is stored in Parquet format in MinIO.
- **Query Layer**: DuckDB queries data directly from MinIO with a caching layer for faster responses.
- **Access Layer**: A backend with GitLab OAuth serves data through a REST API to a Python client and TUMChainBook (JupyterHub).
- **Monitoring**: Prometheus, Loki, and Grafana provide metrics, logs, and dashboards.

## Use Case: MEV Analysis

The pipeline enables MEV analysis by processing and joining on-chain and off-chain data. It supports research into transaction ordering strategies, arbitrage, and gas fee patterns.

## Performance

The system was tested with 60 concurrent users running Jupyter notebooks. Key results:
- Ingestion latency: ~53 seconds
- Cached query latency: ~16 seconds
- CPU usage remained under 80% during peak load

## Technologies

- MinIO for object storage
- DuckDB for lightweight SQL querying
- JupyterHub for user access
- Kubernetes for orchestration
- Prometheus, Loki, and Grafana for monitoring

## Folder Structure

```
pipeline/
├── kubernetes_deployment/
├── module/
├── services/
├── docker-compose.yaml
```

## Code Structure

- **`kubernetes_deployment/`**: Contains Kubernetes manifests and system setup scripts. These are used to provision a fresh machine, install all necessary dependencies (Docker, Kubernetes, Helm, etc.), and deploy the entire pipeline architecture. It enables full production deployment on a cluster from scratch.

- **`modules/`**: Holds the core business logic. This includes all Python modules responsible for data ingestion, data storage (to MinIO), and data access (querying and serving via DuckDB). Organized by functional domain for clarity and modularity.

- **`services/`**: Each subdirectory here contains the `main.py` entry point and `Dockerfile` for building and running the microservices. These are used to start fetchers, processors, or access services as containers.

- **`docker-compose.yaml`**: Defines the services for local deployment. Allows developers to run the full pipeline stack locally using Docker Compose, ideal for testing and development.


## Deployment

The system runs on Kubernetes. See `kubernetes_deployment/` for manifests and deployment instructions.

## Additional Materials

- [Master's Thesis (PDF)](docs/thesis.pdf)
- [Final Talk Slides (PDF)](docs/final-talk.pdf)

