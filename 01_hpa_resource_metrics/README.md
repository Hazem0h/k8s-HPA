# Lab 01: Build an autoscaler based on `metrics.k8s.io` metrics API
* This is based on the [walkthrough](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/#autoscaling-on-multiple-metrics-and-custom-metrics) in the K8s docs

### Prerequisites
* a metrics server. We're using the most basic resources that can be scraped from the kubelets of all nodes. For that, we must have a metrics server, to begin with
    * Metrics server is enabled by default on GKE
    * For minikube, enable the metrics server addon via the `minikube addons enable metrics-server` command

### Steps
1. Deploy the PHP app (deployment + service)
2. Write the code for the pod autoscaler (v1)
3. Simulate a load on the cluster, and watch the number of replicas
    * Try running the following command 
    ```bash
    kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://php-apache; done"
    ```
4. Lower the load, and watch the number of replicas go down.
5. do some curl commands on the `metrics.k8s.io` API and watch for yourself the metrics exposed by the metrics server.

### The HPA yaml file
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-hpa
spec:
  scaleTargetRef:         # The scaling target
    apiVersion: apps/v1
    kind: Deployment      # The deployment name
    name: myapp
  minReplicas: 1
  maxReplicas: 3
  metrics:                # The metrics to scale on (can be an array of metrics. Will pick the one with max replicas,
  - type: Resource        # ... as it would satisfy all
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
```
#### ScaleTargetRef
* This is where we specify the target of the HPA 
#### metrics
* This is where we specify the metrics to scale on
* We can specify an array of metrics, and the HPA will pick the maximum, because it must satisfy all metrics
* Metrics can be of several types, corresponding to different k8s metrics APIs
  * `Resource` => Fetched from the `metrics.k8s.io` API. Currently only has cpu and RAM
  * `Pods` => Fetched from the `custom.metrics.k8s.io` Refers to metrics emited from pods, and scraped from Prometheus. Requires an adapter to register the `custom.metrics.k8s.io` to the Aggregation API, and act as backend for that API.
  * `ContainerResource` => ??
  * `Object` => ??
  * `External` => Fetched from the `external.metrics.k8s.io` API. Still don't know much about it