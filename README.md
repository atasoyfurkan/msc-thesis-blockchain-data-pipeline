# pipeline

 
 ## Helper Commands

 ### Port-forwarding of services

    kubectl port-forward svc/monitoring-grafana 3000:80 -n monitoring

    kubectl port-forward svc/monitoring-kube-prometheus-prometheus 9090:9090 -n monitoring

    kubectl port-forward svc/minio-datalake-console 9091:9090 -n pipeline

    kubectl port-forward svc/api-backend 8000:80 -n pipeline