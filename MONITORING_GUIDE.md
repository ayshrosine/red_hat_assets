# AssetFlow OpenShift - Monitoring Guide

## Overview

This guide provides comprehensive instructions for using OpenShift's built-in monitoring capabilities to observe, troubleshoot, and optimize the AssetFlow application deployment.

## Table of Contents

1. [OpenShift Monitoring Overview](#openshift-monitoring-overview)
2. [Accessing Monitoring Dashboards](#accessing-monitoring-dashboards)
3. [Metrics Monitoring](#metrics-monitoring)
4. [Log Analysis](#log-analysis)
5. [Health Probe Monitoring](#health-probe-monitoring)
6. [Resource Utilization Monitoring](#resource-utilization-monitoring)
7. [Application Performance Monitoring](#application-performance-monitoring)
8. [Alert Configuration](#alert-configuration)
9. [Custom Metrics and Dashboards](#custom-metrics-and-dashboards)
10. [Monitoring Best Practices](#monitoring-best-practices)

---

## OpenShift Monitoring Overview

### Built-in Monitoring Stack

OpenShift provides a comprehensive monitoring stack out of the box:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert management and routing
- **Thanos**: Long-term metrics storage (optional)
- **Node Exporter**: System-level metrics
- **Kube-State-Metrics**: Kubernetes resource metrics

### Key Features

- **Automatic Discovery**: Automatically discovers and monitors Kubernetes resources
- **Pre-built Dashboards**: Ready-to-use dashboards for common scenarios
- **Custom Queries**: PromQL for custom metric queries
- **Alert Rules**: Pre-configured alert rules for common issues
- **Integration**: Seamless integration with OpenShift resources

### Monitoring Architecture

```
┌─────────────────┐
│   Applications  │
│  (Pods/Services)│
└────────┬────────┘
         │ Metrics
         ↓
┌─────────────────┐
│   Prometheus    │
│  (Collection)   │
└────────┬────────┘
         │ Storage
         ↓
┌─────────────────┐
│     Grafana     │
│ (Visualization)│
└────────┬────────┘
         │ Alerts
         ↓
┌─────────────────┐
│  Alertmanager   │
│ (Notification)  │
└─────────────────┘
```

---

## Accessing Monitoring Dashboards

### OpenShift Console Access

1. **Log in to OpenShift Console**
   - Navigate to your OpenShift cluster URL
   - Log in with your credentials

2. **Access Observe Tab**
   - Click on "Observe" in the left navigation panel
   - Select "Monitoring" from the dropdown

3. **Monitoring Dashboard Views**
   - **Metrics**: Real-time metrics visualization
   - **Dashboards**: Pre-built and custom dashboards
   - **Alerts**: Alert rules and notifications
   - **Metrics Targets**: Prometheus targets status

### CLI Access

```bash
# Install monitoring CLI tools (if available)
oc adm must-gather

# Access Prometheus API
oc port-forward svc/prometheus-k8s 9090:9090 -n openshift-monitoring

# Access Grafana
oc port-forward svc/grafana 3000:3000 -n openshift-monitoring
```

### API Access

```bash
# Query Prometheus API
oc exec -n openshift-monitoring prometheus-k8s-0 -- curl -s http://localhost:9090/api/v1/query?query=up

# Get metrics for specific pod
oc exec -n openshift-monitoring prometheus-k8s-0 -- curl -s 'http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total{pod="assetflow-backend-xxxxx"}'
```

---

## Metrics Monitoring

### Key Metrics to Monitor

#### System Metrics
- **CPU Usage**: Container and node CPU utilization
- **Memory Usage**: Container and node memory utilization
- **Network Traffic**: Ingress/egress network traffic
- **Disk I/O**: Storage read/write operations
- **File System Usage**: Disk space utilization

#### Application Metrics
- **Request Rate**: HTTP requests per second
- **Response Time**: Request latency and percentiles
- **Error Rate**: HTTP error rates (4xx, 5xx)
- **Connection Count**: Active connections
- **Thread Count**: Application thread usage

#### Kubernetes Metrics
- **Pod Status**: Pod phase and readiness
- **Replica Count**: Deployment replica counts
- **HPA Status**: Horizontal Pod Autoscaler metrics
- **Resource Quotas**: Namespace resource usage
- **Network Policies**: Network policy rule counts

### Viewing Metrics in Console

1. **Navigate to Metrics**
   - Observe → Monitoring → Metrics

2. **Select Metrics**
   - Choose metric from dropdown or type custom query
   - Common metrics:
     - `container_cpu_usage_seconds_total`
     - `container_memory_working_set_bytes`
     - `rate(http_requests_total[5m])`
     - `rate(http_requests_total{status=~"5.."}[5m])`

3. **Configure Visualization**
   - Select time range (1h, 6h, 24h, 7d)
   - Choose aggregation function (sum, avg, max, min)
   - Add filters for specific resources

### Custom PromQL Queries

#### CPU Utilization
```promql
# CPU usage by pod
sum(rate(container_cpu_usage_seconds_total{pod=~"assetflow-.*"}[5m])) by (pod)

# CPU usage by namespace
sum(rate(container_cpu_usage_seconds_total{namespace="ayshrosine-dev"}[5m])) by (pod)

# CPU percentage
sum(rate(container_cpu_usage_seconds_total{pod=~"assetflow-.*"}[5m])) by (pod) / sum(kube_pod_container_resource_limits{resource="cpu", pod=~"assetflow-.*"}) by (pod) * 100
```

#### Memory Utilization
```promql
# Memory usage by pod
sum(container_memory_working_set_bytes{pod=~"assetflow-.*"}) by (pod)

# Memory percentage
sum(container_memory_working_set_bytes{pod=~"assetflow-.*"}) by (pod) / sum(kube_pod_container_resource_limits{resource="memory", pod=~"assetflow-.*"}) by (pod) * 100
```

#### Application Performance
```promql
# Request rate
rate(http_requests_total{job="assetflow-backend"}[5m])

# Error rate
rate(http_requests_total{job="assetflow-backend", status=~"5.."}[5m])

# Response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="assetflow-backend"}[5m]))
```

### CLI Metrics Commands

```bash
# View resource usage
oc top pods
oc top nodes

# View specific pod metrics
oc top pod assetflow-backend-xxxxx

# View resource usage by namespace
oc top pods -n ayshrosine-dev

# Continuous monitoring
watch oc top pods
```

---

## Log Analysis

### Accessing Logs

#### OpenShift Console
1. Navigate to Observe → Logs
2. Select namespace (ayshrosine-dev)
3. Filter by pod name or label
4. View logs in real-time or historical

#### CLI Commands
```bash
# View logs for specific pod
oc logs assetflow-backend-xxxxx

# View logs for all pods in deployment
oc logs -l app=assetflow-backend

# Follow logs in real-time
oc logs -f assetflow-backend-xxxxx

# View logs from previous pod instance
oc logs assetflow-backend-xxxxx --previous

# View logs with timestamps
oc logs assetflow-backend-xxxxx --timestamps=true

# View last N lines
oc logs assetflow-backend-xxxxx --tail=100
```

### Log Filtering and Analysis

#### Filter by Label
```bash
# Backend logs
oc logs -l app=assetflow-backend

# Frontend logs
oc logs -l app=assetflow-frontend

# Storage demo logs
oc logs -l app=assetflow-backend-storage-demo
```

#### Filter by Time
```bash
# Logs since specific time
oc logs --since-time=2024-01-01T00:00:00Z assetflow-backend-xxxxx

# Logs from last hour
oc logs --since=1h assetflow-backend-xxxxx
```

#### Search Logs
```bash
# Search for errors
oc logs assetflow-backend-xxxxx | grep -i error

# Search for specific requests
oc logs assetflow-backend-xxxxx | grep "GET /api/assets"

# Count error occurrences
oc logs assetflow-backend-xxxxx | grep -i error | wc -l
```

### Log Structuring

#### Application Logs Format
The AssetFlow backend uses structured JSON logging via `deps.py`:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "message": "Request received",
  "method": "GET",
  "path": "/api/assets",
  "status_code": 200,
  "duration_ms": 45
}
```

#### Log Parsing with jq
```bash
# Parse JSON logs
oc logs assetflow-backend-xxxxx | jq '.'

# Filter by log level
oc logs assetflow-backend-xxxxx | jq 'select(.level == "ERROR")'

# Extract specific fields
oc logs assetflow-backend-xxxxx | jq '.message, .status_code'
```

### Log Retention and Management

#### Configure Log Retention
```bash
# Check current log retention settings
oc describe clusterlogging instance

# Log retention is typically managed at cluster level
# Contact cluster administrator for retention policy changes
```

#### Export Logs
```bash
# Export logs to file
oc logs assetflow-backend-xxxxx > backend-logs.txt

# Export all deployment logs
oc logs -l app=assetflow-backend > all-backend-logs.txt

# Export logs with grep
oc logs -l app=assetflow-backend | grep ERROR > error-logs.txt
```

---

## Health Probe Monitoring

### Health Probe Types

#### Liveness Probe
- **Purpose**: Detect if container needs restart
- **Endpoint**: `/healthz`
- **Configuration**: 10s initial delay, 15s period
- **Failure Action**: Restart container

#### Readiness Probe
- **Purpose**: Determine if pod can receive traffic
- **Endpoint**: `/readyz`
- **Configuration**: 5s initial delay, 10s period
- **Failure Action**: Remove from service endpoints

#### Startup Probe
- **Purpose**: Detect slow-starting containers
- **Endpoint**: `/startupz`
- **Configuration**: 30 failure threshold, 5s period
- **Failure Action**: Restart container after 150s

### Monitoring Health Probes

#### Console Monitoring
1. Navigate to Workloads → Pods
2. Click on specific pod
3. View "Container States" section
4. Check "Last State" for restart history

#### CLI Monitoring
```bash
# Check pod status
oc get pods
oc describe pod assetflow-backend-xxxxx

# View restart count
oc get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'

# Check probe status
oc describe pod assetflow-backend-xxxxx | grep -A 20 "Probe"
```

#### Health Endpoint Testing
```bash
# Test health endpoints from within cluster
oc run test-pod --image=curlimages/curl -i --rm --restart=Never -- curl http://assetflow-backend:8000/healthz
oc run test-pod --image=curlimages/curl -i --rm --restart=Never -- curl http://assetflow-backend:8000/readyz
oc run test-pod --image=curlimages/curl -i --rm --restart=Never -- curl http://assetflow-backend:8000/startupz

# Test from external
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/readyz
```

### Health Probe Metrics

#### Probe Success Metrics
```promql
# Liveness probe success rate
sum(rate(probe_success{probe="liveness", pod=~"assetflow-.*"}[5m])) by (pod)

# Readiness probe success rate
sum(rate(probe_success{probe="readiness", pod=~"assetflow-.*"}[5m])) by (pod)

# Startup probe success rate
sum(rate(probe_success{probe="startup", pod=~"assetflow-.*"}[5m])) by (pod)
```

#### Probe Failure Metrics
```promql
# Liveness probe failures
sum(rate(probe_failure{probe="liveness", pod=~"assetflow-.*"}[5m])) by (pod)

# Total probe failures
sum(rate(probe_failure{pod=~"assetflow-.*"}[5m])) by (pod, probe)
```

---

## Resource Utilization Monitoring

### CPU Monitoring

#### Console Monitoring
1. Navigate to Observe → Monitoring → Metrics
2. Query: `container_cpu_usage_seconds_total`
3. Filter by pod: `pod=~"assetflow-.*"`
4. Select rate calculation: `rate(container_cpu_usage_seconds_total[5m])`

#### CLI Monitoring
```bash
# Real-time CPU usage
oc top pods

# Historical CPU usage
oc adm top pods --containers

# CPU usage by node
oc top nodes
```

#### CPU Metrics Queries
```promql
# CPU usage by pod (cores)
sum(rate(container_cpu_usage_seconds_total{pod=~"assetflow-.*"}[5m])) by (pod)

# CPU usage percentage
sum(rate(container_cpu_usage_seconds_total{pod=~"assetflow-.*"}[5m])) by (pod) / sum(kube_pod_container_resource_limits{resource="cpu", pod=~"assetflow-.*"}) by (pod) * 100

# CPU usage by deployment
sum(rate(container_cpu_usage_seconds_total{pod=~"assetflow-backend-.*"}[5m]))
```

### Memory Monitoring

#### Console Monitoring
1. Navigate to Observe → Monitoring → Metrics
2. Query: `container_memory_working_set_bytes`
3. Filter by pod: `pod=~"assetflow-.*"`

#### CLI Monitoring
```bash
# Real-time memory usage
oc top pods

# Memory usage by container
oc adm top pods --containers

# Memory usage by node
oc top nodes
```

#### Memory Metrics Queries
```promql
# Memory usage by pod (bytes)
sum(container_memory_working_set_bytes{pod=~"assetflow-.*"}) by (pod)

# Memory usage percentage
sum(container_memory_working_set_bytes{pod=~"assetflow-.*"}) by (pod) / sum(kube_pod_container_resource_limits{resource="memory", pod=~"assetflow-.*"}) by (pod) * 100

# Memory usage by deployment
sum(container_memory_working_set_bytes{pod=~"assetflow-backend-.*"})
```

### Network Monitoring

#### Network Metrics Queries
```promql
# Network receive bytes by pod
sum(rate(container_network_receive_bytes_total{pod=~"assetflow-.*"}[5m])) by (pod)

# Network transmit bytes by pod
sum(rate(container_network_transmit_bytes_total{pod=~"assetflow-.*"}[5m])) by (pod)

# Network receive errors
sum(rate(container_network_receive_errors_total{pod=~"assetflow-.*"}[5m])) by (pod)

# Network transmit errors
sum(rate(container_network_transmit_errors_total{pod=~"assetflow-.*"}[5m])) by (pod)
```

### Storage Monitoring

#### Storage Metrics Queries
```promql
# Disk usage by pod
sum(container_fs_usage_bytes{pod=~"assetflow-.*"}) by (pod)

# Disk I/O read bytes
sum(rate(container_fs_reads_bytes_total{pod=~"assetflow-.*"}[5m])) by (pod)

# Disk I/O write bytes
sum(rate(container_fs_writes_bytes_total{pod=~"assetflow-.*"}[5m])) by (pod)
```

---

## Application Performance Monitoring

### HTTP Request Monitoring

#### Request Rate
```promql
# Total request rate
rate(http_requests_total{job="assetflow-backend"}[5m])

# Request rate by endpoint
rate(http_requests_total{job="assetflow-backend"}[5m]) by (path)

# Request rate by status code
rate(http_requests_total{job="assetflow-backend"}[5m]) by (status)
```

#### Response Time
```promql
# Average response time
rate(http_request_duration_seconds_sum{job="assetflow-backend"}[5m]) / rate(http_request_duration_seconds_count{job="assetflow-backend"}[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="assetflow-backend"}[5m]))

# 99th percentile response time
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{job="assetflow-backend"}[5m]))
```

#### Error Rate
```promql
# Total error rate
rate(http_requests_total{job="assetflow-backend", status=~"5.."}[5m])

# Error rate by endpoint
rate(http_requests_total{job="assetflow-backend", status=~"5.."}[5m]) by (path)

# Error percentage
rate(http_requests_total{job="assetflow-backend", status=~"5.."}[5m]) / rate(http_requests_total{job="assetflow-backend"}[5m]) * 100
```

### Database Performance Monitoring

#### MongoDB Metrics (if available)
```promql
# MongoDB operation rate
rate(mongodb_op_counters_total[5m])

# MongoDB connection count
mongodb_connections_count

# MongoDB memory usage
mongodb_memory_resident_bytes
```

### Custom Application Metrics

#### Adding Custom Metrics
```python
# In backend application
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('active_connections', 'Active database connections')

# Use metrics in code
@app.get("/api/assets")
async def get_assets():
    with request_duration.time():
        # Your code here
        request_count.labels(method='GET', endpoint='/api/assets', status=200).inc()
        return {"assets": []}
```

---

## Alert Configuration

### Pre-configured Alerts

OpenShift includes pre-configured alerts for common scenarios:

- **PodCrashLooping**: Pod is crash looping
- **PodNotReady**: Pod is not ready
- **HighCPUUsage**: CPU usage above threshold
- **HighMemoryUsage**: Memory usage above threshold
- **DiskSpaceLow**: Disk space running low
- **ReplicaSetMismatch**: Replica count mismatch

### Viewing Alerts

#### Console Access
1. Navigate to Observe → Monitoring → Alerts
2. View active and firing alerts
3. Click on alert for details
4. View alert history and trends

#### CLI Access
```bash
# View alert rules
oc get prometheusrules -n openshift-monitoring

# View alerting rules
oc get alertingrules -n openshift-monitoring

# View silences
oc get silences -n openshift-monitoring
```

### Custom Alert Rules

#### Create Custom Alert Rule
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: assetflow-alerts
  namespace: ayshrosine-dev
spec:
  groups:
    - name: assetflow.rules
      rules:
        - alert: HighErrorRate
          expr: rate(http_requests_total{job="assetflow-backend", status=~"5.."}[5m]) > 0.1
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High error rate detected"
            description: "Error rate is {{ $value }} errors/sec"
```

#### Apply Custom Alert Rule
```bash
oc apply -f assetflow-alerts.yaml
```

### Alert Notifications

#### Configure Notification Channels
1. Navigate to Observe → Monitoring → Alerting
2. Configure notification channels (Email, Slack, PagerDuty)
3. Create notification routes
4. Test notification delivery

---

## Custom Metrics and Dashboards

### Creating Custom Dashboards

#### Using Grafana
1. Navigate to Observe → Monitoring → Dashboards
2. Click "Create Dashboard"
3. Add panels with custom queries
4. Configure visualization options
5. Save and share dashboard

#### Example Dashboard Panels

**Panel 1: Request Rate**
```promql
sum(rate(http_requests_total{job="assetflow-backend"}[5m]))
```

**Panel 2: Error Rate**
```promql
sum(rate(http_requests_total{job="assetflow-backend", status=~"5.."}[5m]))
```

**Panel 3: Response Time**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="assetflow-backend"}[5m]))
```

**Panel 4: CPU Usage**
```promql
sum(rate(container_cpu_usage_seconds_total{pod=~"assetflow-backend-.*"}[5m]))
```

**Panel 5: Memory Usage**
```promql
sum(container_memory_working_set_bytes{pod=~"assetflow-backend-.*"})
```

### Importing Dashboards

#### Import Pre-built Dashboards
1. Navigate to Observe → Monitoring → Dashboards
2. Click "Import Dashboard"
3. Paste dashboard JSON or upload file
4. Select data source (Prometheus)
5. Import and customize

#### Exporting Dashboards
1. Navigate to dashboard
2. Click "Share" → "Export"
3. Copy JSON or download file
4. Save for backup or sharing

---

## Monitoring Best Practices

### Metrics Collection

#### DO:
- Collect relevant metrics for your use case
- Use appropriate metric types (Counter, Gauge, Histogram)
- Label metrics consistently
- Keep metric cardinality reasonable
- Document metric meanings

#### DON'T:
- Collect too many metrics (performance impact)
- Use high-cardinality labels
- Create metrics without clear purpose
- Ignore metric retention costs
- Mix metric types incorrectly

### Alert Configuration

#### DO:
- Set appropriate thresholds based on baselines
- Use alert severity levels appropriately
- Include clear alert descriptions
- Test alert rules before production
- Configure notification channels

#### DON'T:
- Set thresholds too low (alert fatigue)
- Create alerts without action plans
- Ignore alert tuning
- Forget to test alert delivery
- Over-alert on non-critical issues

### Dashboard Design

#### DO:
- Design dashboards for specific audiences
- Use consistent color schemes
- Include relevant context and annotations
- Keep dashboards simple and focused
- Regularly review and update dashboards

#### DON'T:
- Create overly complex dashboards
- Use too many colors or visual elements
- Clutter dashboards with irrelevant data
- Ignore performance impact
- Set and forget dashboards

### Log Management

#### DO:
- Use structured logging formats
- Include relevant context in logs
- Set appropriate log levels
- Implement log rotation
- Monitor log volume and costs

#### DON'T:
- Log sensitive information
- Use excessive logging (performance impact)
- Ignore log parsing and analysis
- Forget log retention policies
- Log without clear purpose

### Performance Monitoring

#### DO:
- Monitor application performance proactively
- Set up performance baselines
- Monitor end-user experience
- Correlate metrics with logs
- Use distributed tracing if needed

#### DON'T:
- Focus only on infrastructure metrics
- Ignore performance degradation
- Monitor in isolation
- Forget to monitor third-party dependencies
- Over-complicate monitoring setup

---

## Monitoring Quick Reference

### Essential Commands
```bash
# Resource usage
oc top pods
oc top nodes

# Logs
oc logs <pod-name>
oc logs -l app=assetflow-backend
oc logs -f <pod-name>

# Pod status
oc get pods
oc describe pod <pod-name>

# Events
oc get events --sort-by='.lastTimestamp'

# Scaling
oc get hpa
oc describe hpa assetflow-backend-hpa
```

### Key Metrics to Monitor
- CPU utilization (pod and node level)
- Memory utilization (pod and node level)
- Request rate and error rate
- Response time (p50, p95, p99)
- Pod restart counts
- Health probe success rates
- Network traffic and errors
- Disk I/O and usage

### Critical Alerts to Set Up
- High error rate (>5%)
- High response time (>1s p95)
- High CPU usage (>80%)
- High memory usage (>90%)
- Pod crash looping
- Pod not ready for extended time
- Replica count mismatch
- Disk space running low

---

## Troubleshooting Monitoring Issues

### Metrics Not Appearing

#### Diagnosis
```bash
# Check Prometheus targets
oc get prometheus -n openshift-monitoring
oc describe prometheus k8s -n openshift-monitoring

# Check if pods are being scraped
oc exec -n openshift-monitoring prometheus-k8s-0 -- wget -qO- http://localhost:9090/api/v1/targets
```

#### Solutions
1. Verify pods have correct labels
2. Check Prometheus service monitors
3. Ensure pods are running
4. Check network policies
5. Verify Prometheus configuration

### Logs Not Appearing

#### Diagnosis
```bash
# Check if logging stack is running
oc get pods -n openshift-logging

# Check log forwarding
oc get clusterlogging instance
```

#### Solutions
1. Verify logging stack is installed
2. Check pod status and logs
3. Verify log permissions
4. Check network policies
5. Review logging configuration

### Alerts Not Firing

#### Diagnosis
```bash
# Check alert rules
oc get prometheusrules -n openshift-monitoring

# Check alerting rules
oc get alertingrules -n openshift-monitoring

# Check silences
oc get silences -n openshift-monitoring
```

#### Solutions
1. Verify alert rule syntax
2. Check alert rule evaluation
3. Review alert thresholds
4. Check for silences
5. Verify notification channel configuration

---

## Conclusion

This monitoring guide provides comprehensive coverage of OpenShift's built-in monitoring capabilities for the AssetFlow application. By following these practices, you can effectively monitor, troubleshoot, and optimize your deployment.

Regular monitoring and analysis of metrics and logs will help ensure the reliability, performance, and availability of your application in production.

For additional information, refer to:
- OpenShift Monitoring Documentation: https://docs.openshift.com/container-platform/latest/monitoring/
- Prometheus Documentation: https://prometheus.io/docs/
- Grafana Documentation: https://grafana.com/docs/