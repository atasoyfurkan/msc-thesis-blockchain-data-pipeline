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

# Deploy shared configs
kubectl apply -f shared_configmap.yaml
kubectl apply -f shared_secret.yaml

# Deploy api-backend
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-api-backend:v1.0 \
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
  -t atasoy/pipeline-mempool-fetcher:v1.7 \
  --file ../services/mempool_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f mempool_fetcher/deployment.yaml

# Deploy block-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-block-fetcher:v1.2 \
  --file ../services/block_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f block_fetcher/deployment.yaml

# Deploy price-data-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-price-data-fetcher:v1.3 \
  --file ../services/price_data_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f price_data_fetcher/deployment.yaml

# Deploy transfer-event-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-transfer-event-fetcher:v1.1 \
  --file ../services/transfer_event_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f transfer_event_fetcher/deployment.yaml

# Install prometheus and grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl apply -f monitoring/prometheus-grafana/namespace.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/minio-bucket-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/minio-cluster-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/jupyterhub-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/jupyterhub-user-diagnostic-dashboard-configmap.yaml
sudo mount --make-rshared / # allowing mount events to propagate between namespaces (necessary for Kubernetes) 
helm upgrade --install \
    --namespace monitoring \
    --create-namespace \
    --values monitoring/prometheus-grafana/values.yaml \
    monitoring prometheus-community/kube-prometheus-stack 

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