# pipeline

 
 ## Helper Commands

 ### Port-forwarding of services

    kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

    kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9092:9090 -n monitoring

    kubectl port-forward svc/minio-datalake-console 9091:9090 -n pipeline

    kubectl port-forward svc/api-backend 8000:80 -n pipeline

### Kubectl change default namespace

   kubectl config set-context --current --namespace=

### Get folder storage usage linux

   du -h --max-depth=1

### Pre-pull images if it stucks

   sudo ctr images pull docker.io/atasoy/pipeline-api-backend:v1.4