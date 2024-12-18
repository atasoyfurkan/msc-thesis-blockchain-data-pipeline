# Install helm
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# Deploy minio
## Install minio-operator
helm repo add minio-operator https://operator.min.io
helm upgrade --install \
    --namespace minio-operator \
    --create-namespace \
    operator minio-operator/operator

## Install minio-tenant
helm upgrade --install \
    --namespace pipeline \
    --create-namespace \
    --values minio/values.yaml \
    myminio minio-operator/tenant

# Deploy shared configs
kubectl apply -f shared_configmap.yaml
kubectl apply -f shared_secret.yaml

# Deploy api-backend
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-api-backend:latest \
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
  -t atasoy/pipeline-mempool-fetcher:latest \
  --file ../services/mempool_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f mempool_fetcher/deployment.yaml

# Deploy price_data-fetcher
## Build and push docker image
docker buildx build --platform linux/amd64 \
  -t atasoy/pipeline-price-data-fetcher:latest \
  --file ../services/price_data_fetcher/Dockerfile \
  ../ \
  --push
## Apply kubernetes manifests
kubectl apply -f price_data_fetcher/deployment.yaml

# Install prometheus and grafana
# TODO: increase storage for prometheus when you move to production node
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl apply -f monitoring/prometheus-grafana/dashboards/minio-bucket-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/minio-cluster-dashboard-configmap.yaml
kubectl apply -f monitoring/prometheus-grafana/dashboards/jupyterhub-dashboard-configmap.yaml
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