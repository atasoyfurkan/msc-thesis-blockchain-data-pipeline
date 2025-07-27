# Kubernetes Deployment

This folder contains all configuration and automation scripts required to deploy the blockchain data pipeline on a Kubernetes cluster.

## Overview

The deployment process is configured for the infrastructure at the Chair of Network Architectures and Services, where machines lose installed system dependencies on reboot but preserve Kubernetes state.

## Deployment Scripts

You can use one of the two provided scripts to deploy the system:

### `install.bootstrap.sh`

Use this script to **set up a new machine from scratch**. It will:
- Install necessary system dependencies (Docker, Kubernetes, Helm, etc.)
- Apply all Kubernetes manifests to deploy the pipeline components

**Usage:**
```bash
./install.bootstrap.sh
```

Run this when initializing a completely new machine.

---

### `install.reboot.sh`

Use this script **after a machine reboot**, when system packages need to be reinstalled but Kubernetes state is still intact.

It will:
- Reinstall required system dependencies
- Skip applying Kubernetes manifests (since they persist across reboots)

**Usage:**
```bash
./install.reboot.sh
```

Run this script after any reboot on the Network Chair infrastructure machines.

## Structure

- `api_backend/`, `fetchers/`, `minio/`, `monitoring/`: Kubernetes manifests grouped by functionality
- `server_setup/`: Additional configuration or provisioning files
- `simulators/`: Kubernetes statefulsets for simulating traffic and testing
- `shared_pipeline_configmap.yaml`, `shared_pipeline_secret.yaml`: Shared environment config and secrets for all services

## Notes

Ensure you have execution permission before running the scripts:
```bash
chmod +x install.bootstrap.sh install.reboot.sh
```
