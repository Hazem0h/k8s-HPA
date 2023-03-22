

### Explanation. Refer to this [link](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/)
#### Everything is a URL (API) in k8s
* According to the [docs](https://kubernetes.io/docs/reference/using-api/),
>* The REST API is the fundamental fabric of Kubernetes. All operations and communications between components, and external user commands are REST API calls that the API Server handles. Consequently, everything in the Kubernetes platform is treated as an API object and has a corresponding entry in the API 

* So, a deployment is an API, a service is an API, 
* There's also the **Metrics API**

#### The Metrics API
* One of these APIs is the metrics API, which is a front for querying metrics inside the k8s cluster
* These metrics need to be in the form of an API such that other k8s components can consume them, like the Horizontal Pod Autoscler
* As we know beforehand, metrics are very important for monitoring
* However, by default the metrics API isn't part of the k8s cluster. We will have to add it ourselves (except for managed services, like GKE)

* K8s supports API definitions (interfaces) for Several Metrics APIs
    * [Resource Metrics API](https://github.com/kubernetes/metrics/tree/master/pkg/apis/metrics) => `metrics.k8s.io` [design proposal Documet](https://github.com/kubernetes/design-proposals-archive/blob/main/instrumentation/resource-metrics-api.md)
    * [Custom Metrics API](https://github.com/kubernetes/metrics/tree/master/pkg/apis/custom_metrics) => ??
    * [External Metrics API](https://github.com/kubernetes/metrics/tree/master/pkg/apis/external_metrics) => ??
* These definitions are like protobuff definitions. Developers of monitoring software can implement a backend/addon/adapter that implements this interface, and adds it to the Aggregation layer

#### Why metrics are useful
* As we know previously, metrics are essential for monitoring, alerting and debugging.
* In k8s, they can also trigger horizontal scaling of pods, via the Horizontal Pod Autoscaler.

#### Why a metrics API in k8s, why not just consume the prometheus metrics?
* The thing is we want the prometheus metrics to be consumed by a k8s component. They must be in the form of an API that k8s HPA understands
* Prometheus itself scrapes metrics, and offers other to query it using PromQL. This isn't sufficient to make it an API compatible with k8s. Therefore we need some form of an `adapter`

#### How to add an API to k8s?
* To add an API, we must register it in the [`API aggregation Layer`](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/apiserver-aggregation/)
* We must also have a backend that implements the API itself.
* For simple CPU and RAM metrics, we can deploy a metrics server, which acts as a prometheus server + adapter for simple metrics

#### The default k8s [metrics server](https://github.com/kubernetes-sigs/metrics-server#deployment)
* So, deploying the metrics server does the following
    * Regsiters the `metrics.k8s.io` API to the `API aggregation Layer`
    * Acts as backend for the `metrics.k8s.io` API, via
        * Scraping metrics from kubelet


#### Metrics Server = simple Prometheus + Adapter?
From chatGPT:
> The Kubernetes Metrics Server and Prometheus with its adapter have some similarities, but they serve different purposes.

>The Kubernetes Metrics Server is a lightweight, low-overhead monitoring solution that provides resource utilization metrics for Kubernetes objects, such as pods and nodes. It collects metrics directly from the Kubernetes API server and stores them in memory, rather than persisting them to a database like Prometheus does. The Metrics Server is primarily designed to support features like Horizontal Pod Autoscaler (HPA) and Kubernetes Dashboard, which use these metrics to make scaling and monitoring decisions.

* The metrics server is only meant as a lightweight metric collector for HPA and VPA.
* If you want non-scaling options, scrape the kubelet metrics via a more sophisticated tool, like prometheus

#### How the resource metrics pipeline works
![image](/images/resource-metrics.png)

* K8s uses `cAdvisor` to extract metrics from the containers. 
* Kubelet can then expose those metrics scraped from `cAdvisor`, as well as other metrics from the pods and the nodes
* The metrics server takes these metrics from kubelet, and exposes as the `metrics.k8s.io` metric API

#### Demo: Sending HTTP requests to the metrics API 
* After running the metrics server, we can run HTTP requests against the `metrics.k8s.io` API, like so

```bash
# Command Querying the metric API over node metrics
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes/minikube" | jq '.'
```
```json
//Output:
{
  "kind": "NodeMetrics",
  "apiVersion": "metrics.k8s.io/v1beta1",
  "metadata": {
    "name": "minikube",
    "creationTimestamp": "2023-03-21T20:02:35Z",
    "labels": {
      "beta.kubernetes.io/arch": "amd64",
      "beta.kubernetes.io/os": "linux",
      "gcs.csi.ofek.dev/driver-ready": "true",
      "kubernetes.io/arch": "amd64",
      "kubernetes.io/hostname": "minikube",
      "kubernetes.io/os": "linux",
      "minikube.k8s.io/commit": "986b1ebd987211ed16f8cc10aed7d2c42fc8392f",
      "minikube.k8s.io/name": "minikube",
      "minikube.k8s.io/primary": "true",
      "minikube.k8s.io/updated_at": "2023_02_20T21_17_27_0700",
      "minikube.k8s.io/version": "v1.28.0",
      "node-role.kubernetes.io/control-plane": "",
      "node.kubernetes.io/exclude-from-external-load-balancers": ""
    }
  },
  "timestamp": "2023-03-21T20:02:04Z",
  "window": "1m11.109s",
  "usage": {
    "cpu": "129229492n",
    "memory": "1104172Ki"
  }
}
```
We can query on pods, replace the /nodes route with /pods route and see for yourself

#### The Auto-Scaling [algorithm exaplained](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/#algorithm-details)
`desiredReplicas = ceil[currentReplicas * ( currentMetricValue / desiredMetricValue )]`
* Let's assume the metrics value is something like the cpu utilization
* Let's say the desired average utilization is 50%
  * This means that when the utilization is below, say like 10%, this means we are wasting resources, and should scale down
  * According to the equation, the scaling factor will be 1/5. So, the number of replicas will be `ceil(currentReplicas * scalingFactor)
  * If the utilization is very high, say like 70%, this will trigger the scaling up.
  * According to the equation, the scaling factor will be 7/5
* We can interpret other metrics the same
  * latency => if it's low, this means we don't need extra replicas (we can scale down), if it's high, we need extra replicas (scale up)

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

