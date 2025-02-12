#!/bin/bash

##### Installation #####

./install.reboot.sh


##### Kubernetes Deployments #####

# Install nginx ingress controller using helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# apply cert-manager and cluster issuer
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.5.0/cert-manager.yaml
kubectl apply -f server_setup/cluster-issuer-letsencrypt.yaml

# Deploy minio
## Install minio-operator
helm repo add minio-operator https://operator.min.io
helm upgrade --install \
    --namespace minio-operator \
    --create-namespace \
    operator minio-operator/operator

## Install nfs-provisioner for minio-datalake
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
helm install nfs-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
  --namespace pipeline \
  --create-namespace \
  --set nfs.server=192.168.242.1 \
  --set nfs.path=/pipeline_minio_data \
  --set storageClass.name=nfs-storage-class

## Install minio-tenant
helm upgrade --install \
    --namespace pipeline \
    --create-namespace \
    --values minio/values.yaml \
    minio-datalake minio-operator/tenant

# Deploy shared configs for pipeline
kubectl apply -f shared_pipeline_configmap.yaml
kubectl apply -f shared_pipeline_secret.yaml

# Deploy api-backend
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-api-backend:v1.10 \
  --file ../services/api_backend/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f api_backend/deployment.yaml
kubectl apply -f api_backend/service.yaml
kubectl apply -f api_backend/ingress.yaml

# Deploy mempool-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-mempool-fetcher:v1.10 \
  --file ../services/fetchers/mempool_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f fetchers/mempool_fetcher/deployment.yaml

# Deploy block-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-block-fetcher:v1.5 \
  --file ../services/fetchers/block_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f fetchers/block_fetcher/deployment.yaml

# Deploy price-data-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-price-data-fetcher:v1.6 \
  --file ../services/fetchers/price_data_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f fetchers/price_data_fetcher/deployment.yaml

# Deploy transfer-event-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-transfer-event-fetcher:v1.6 \
  --file ../services/fetchers/transfer_event_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f fetchers/transfer_event_fetcher/deployment.yaml

# Create namespace for simulators
kubectl create namespace simulator

# Deploy shared configs for simulators
kubectl apply -f simulators/shared_simulator_configmap.yaml
kubectl apply -f simulators/shared_simulator_secret.yaml

# Deploy trade-researcher-simulator
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-trade-researcher-simulator:v1.2 \
  --file ../services/simulators/trade_researcher_simulator/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f simulators/trade_researcher_simulator/deployment.yaml

# Install prometheus and grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl apply -f monitoring/prometheus-grafana/namespace.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/minio-bucket-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/minio-cluster-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/jupyterhub-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/jupyterhub-user-diagnostic-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/evaluation-metrics-data-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/evaluation-metrics-resource-dashboard-configmap.yaml
sudo mount --make-rshared / # allowing mount events to propagate between namespaces (necessary for Kubernetes) 
helm upgrade --install \
    --namespace monitoring \
    --create-namespace \
    --values monitoring/prometheus-grafana/values.yaml \
    monitoring prometheus-community/kube-prometheus-stack 
## Install prometheus-pushgateway for fetchers to push metrics
helm upgrade --install prometheus-pushgateway prometheus-community/prometheus-pushgateway \
  --namespace monitoring \
  --create-namespace


# Install loki and promtail
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install \
    --namespace monitoring \
    --create-namespace \
    --values monitoring/loki-promtail/values-loki.yaml \
    loki grafana/loki
helm upgrade --install \
    --namespace monitoring \
    --create-namespace \
    --values monitoring/loki-promtail/values-promtail.yaml \
    promtail grafana/promtail