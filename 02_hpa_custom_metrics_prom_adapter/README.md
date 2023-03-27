# Using Custom Metrics 
Adapted From Techworld with Nana, using these videos:
* [Video 1](https://www.youtube.com/watch?v=QoDqxm7ybLc&ab_channel=TechWorldwithNana)
* [Video 2](https://www.youtube.com/watch?v=mLPg49b33sA&ab_channel=TechWorldwithNana)


## Deploying Prometheus on K8s [Using Helm Chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
* Add the repo
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```
* Then install the chartprom-operator
```Bash
helm install prometheus prometheus-community/kube-prometheus-stack --create-namespace -n monitoring
```
This includes a stack of 
* Prometheus Operator
* Node Exporter (TODO: remove it, not necessary)
* Prometheus adapter
* Grafana
* Kube-state-metrics

### How to make your apps discoverable?
The aforementioned stack has some CRDs. They define the logic of service discovery. By default,
* You must a `ServiceMonitor` resource, with `release: prometheus` label
* The `ServiceMonitor` should point to the application's metrics endpoint

## Choose the APP and the metric to scale upon
* We can install a dummy app that emits static metrics, configurable from environment variables
* We will see how autoscaling behaves due to this metric
* The app is in `app.py`
    * It has a gauge metric which is fixed at `40`.
    * The http server itself is at port `8000`
    * The metrics endpoint is at port `9000` and has the path: `/metrics`
* I have built a docker image for the app, and pushed it to Dockerhub
* I then created a k8s deployment for this app, and made sure it's metrics port is working correctly

## Add Service Monitoring for Prometheus to discover the app
* Now that prometheus and the app are on k8s, we want k8s to discover the app
* We need a ServiceMonitor component for that
## Install the Prometheus adapter
```bash
helm install prometheus-adapter prometheus-community/prometheus-adapter
```

## Simulate Load, and see the autoscaler in action