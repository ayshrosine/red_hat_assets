# AssetFlow OpenShift - Troubleshooting Guide

## Overview

This guide provides comprehensive troubleshooting procedures for common issues that may occur during deployment, operation, or demonstration of the AssetFlow application on Red Hat OpenShift.

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Pod and Container Issues](#pod-and-container-issues)
3. [Networking and Connectivity Issues](#networking-and-connectivity-issues)
4. [Authentication and Authorization Issues](#authentication-and-authorization-issues)
5. [Storage and PVC Issues](#storage-and-pvc-issues)
6. [Performance and Scaling Issues](#performance-and-scaling-issues)
7. [Monitoring and Logging Issues](#monitoring-and-logging-issues)
8. [Security Issues](#security-issues)
9. [CI/CD Pipeline Issues](#cicd-pipeline-issues)
10. [Frontend Issues](#frontend-issues)
11. [Serverless Function Issues](#serverless-function-issues)

---

## Deployment Issues

### Issue: Image Pull Errors

**Symptoms**:
- Pods stuck in `ImagePullBackOff` or `ErrImagePull` state
- Error messages about failed image pulls
- Pods not starting after deployment

**Diagnosis**:
```bash
# Check pod status
oc get pods
oc describe pod <failing-pod>

# Check events
oc get events --sort-by='.lastTimestamp'
```

**Solutions**:

1. **Verify Image Registry Access**
```bash
# Test image pull manually
docker pull ghcr.io/ayshrosine/assetflow-backend:latest
docker pull ghcr.io/ayshrosine/assetflow-frontend:latest
```

2. **Check Image Pull Secrets**
```bash
# Verify secrets exist
oc get secrets
oc describe secret <pull-secret-name>

# Create/update pull secret if needed
oc create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token>
```

3. **Verify Image Tags**
```bash
# Check deployment image references
oc get deployment assetflow-backend -o jsonpath='{.spec.template.spec.containers[0].image}'
oc get deployment assetflow-frontend -o jsonpath='{.spec.template.spec.containers[0].image}'
```

4. **Update Deployment with Correct Image**
```bash
oc set image deployment/assetflow-backend backend=ghcr.io/ayshrosine/assetflow-backend:latest
oc set image deployment/assetflow-frontend frontend=ghcr.io/ayshrosine/assetflow-frontend:latest
```

### Issue: Deployment Not Updating

**Symptoms**:
- Changes to deployment not reflected in running pods
- Old pods still running after deployment update
- Rolling update stuck

**Diagnosis**:
```bash
# Check deployment status
oc get deployment assetflow-backend
oc describe deployment assetflow-backend

# Check rollout status
oc rollout status deployment/assetflow-backend
```

**Solutions**:

1. **Force Rollout**
```bash
oc rollout restart deployment/assetflow-backend
oc rollout status deployment/assetflow-backend
```

2. **Check Rollout History**
```bash
oc rollout history deployment/assetflow-backend
oc rollout undo deployment/assetflow-backend
```

3. **Update Image with New Tag**
```bash
oc set image deployment/assetflow-backend backend=ghcr.io/ayshrosine/assetflow-backend:<new-tag>
oc rollout status deployment/assetflow-backend
```

4. **Delete Stuck Pods**
```bash
oc delete pod <stuck-pod-name>
# Let deployment recreate it
```

---

## Pod and Container Issues

### Issue: Pods Stuck in Pending State

**Symptoms**:
- Pods remain in `Pending` state indefinitely
- No containers running
- Events show scheduling issues

**Diagnosis**:
```bash
# Check pod status
oc get pods
oc describe pod <pending-pod>

# Check node resources
oc top nodes
oc describe nodes
```

**Solutions**:

1. **Check Resource Quotas**
```bash
# Check resource quotas in namespace
oc get resourcequota
oc describe resourcequota

# Check pod resource requests
oc describe pod <pending-pod> | grep -A 10 "Resources"
```

2. **Adjust Resource Requests**
```bash
# Edit deployment to reduce resource requests
oc edit deployment assetflow-backend

# Reduce CPU/memory requests if quota exceeded
```

3. **Check Node Availability**
```bash
# Check if nodes are available
oc get nodes
oc describe nodes
```

4. **Check Taints and Tolerations**
```bash
# Check node taints
oc describe nodes | grep -A 5 "Taints"

# Check pod tolerations
oc describe pod <pending-pod> | grep -A 5 "Tolerations"
```

### Issue: Pods Crashing or Restarting

**Symptoms**:
- Pods in `CrashLoopBackOff` state
- High restart counts
- Containers starting and failing repeatedly

**Diagnosis**:
```bash
# Check pod status and restart count
oc get pods
oc describe pod <crashing-pod>

# Check container logs
oc logs <crashing-pod>
oc logs <crashing-pod> --previous
```

**Solutions**:

1. **Check Application Logs**
```bash
# View recent logs
oc logs <crashing-pod> --tail=50

# Follow logs in real-time
oc logs -f <crashing-pod>
```

2. **Check Environment Variables**
```bash
# Verify environment variables are set
oc describe pod <crashing-pod> | grep -A 20 "Environment"

# Check ConfigMaps and Secrets
oc get configmaps
oc get secrets
oc describe configmap assetflow-config
oc describe secret assetflow-secrets
```

3. **Verify Database Connectivity**
```bash
# Test database connection from pod
oc exec -it <backend-pod> -- python -c "from deps import db; print(db.command('ping'))"
```

4. **Check Health Probe Configuration**
```bash
# Verify health endpoints are accessible
oc exec -it <backend-pod> -- curl http://localhost:8000/healthz
oc exec -it <backend-pod> -- curl http://localhost:8000/readyz
```

5. **Adjust Startup Probe**
```bash
# If application takes longer to start, increase startup probe thresholds
oc edit deployment assetflow-backend
# Increase failureThreshold or periodSeconds in startupProbe
```

### Issue: Containers Not Ready

**Symptoms**:
- Pods running but containers not ready
- Readiness probe failing
- Traffic not routed to pods

**Diagnosis**:
```bash
# Check pod readiness
oc get pods
oc describe pod <not-ready-pod>

# Check readiness probe status
oc describe pod <not-ready-pod> | grep -A 10 "Readiness"
```

**Solutions**:

1. **Test Readiness Endpoint Manually**
```bash
oc exec -it <backend-pod> -- curl http://localhost:8000/readyz
```

2. **Check Dependencies**
```bash
# Verify database is accessible
oc exec -it <backend-pod> -- python -c "from deps import db; print(db.command('ping'))"

# Verify external services are reachable
oc exec -it <backend-pod> -- curl -I https://www.googleapis.com
```

3. **Adjust Readiness Probe**
```bash
# Edit deployment to adjust readiness probe
oc edit deployment assetflow-backend
# Increase initialDelaySeconds or periodSeconds
```

---

## Networking and Connectivity Issues

### Issue: Services Not Accessible

**Symptoms**:
- Services not responding
- Connection timeouts
- 503 errors from routes

**Diagnosis**:
```bash
# Check service status
oc get services
oc describe service assetflow-backend
oc describe service assetflow-frontend

# Check service endpoints
oc get endpoints assetflow-backend
oc get endpoints assetflow-frontend
```

**Solutions**:

1. **Verify Pod Selector Match**
```bash
# Check service selector
oc get service assetflow-backend -o jsonpath='{.spec.selector}'

# Check pod labels
oc get pods -l app=assetflow-backend --show-labels

# Labels must match exactly
```

2. **Check Endpoint Configuration**
```bash
# Verify endpoints are populated
oc get endpoints assetflow-backend

# If empty, check if pods are ready
oc get pods -l app=assetflow-backend
```

3. **Test Service Internally**
```bash
# Test service from within cluster
oc run test-pod --image=curlimages/curl -i --rm --restart=Never -- curl http://assetflow-backend:8000/healthz
```

### Issue: Routes Not Working

**Symptoms**:
- Routes not accessible from browser
- Connection refused
- DNS resolution failures

**Diagnosis**:
```bash
# Check route status
oc get routes
oc describe route assetflow-frontend
oc describe route assetflow-backend

# Check route hostnames
oc get route assetflow-frontend -o jsonpath='{.spec.host}'
```

**Solutions**:

1. **Verify Route Configuration**
```bash
# Check route specifies correct service
oc describe route assetflow-frontend

# Verify port configuration
oc describe route assetflow-frontend | grep -A 5 "Port"
```

2. **Check TLS/SSL Configuration**
```bash
# Verify TLS certificate
oc describe route assetflow-frontend | grep -A 10 "TLS"

# Test with curl
curl -k https://assetflow-frontend-.../
```

3. **Verify DNS Resolution**
```bash
# Test DNS resolution
nslookup assetflow-frontend-...apps.openshiftapps.com
dig assetflow-frontend-...apps.openshiftapps.com
```

4. **Check Router Pod**
```bash
# Check router pod is running
oc get pods -n openshift-ingress

# Check router logs
oc logs -n openshift-ingress <router-pod-name>
```

### Issue: Network Policy Blocking Traffic

**Symptoms**:
- Pods not communicating
- Connection timeouts between services
- Network policy denied events

**Diagnosis**:
```bash
# Check network policies
oc get networkpolicy
oc describe networkpolicy default-deny-all

# Check pod events for network policy denials
oc describe pod <affected-pod> | grep -i "network"
```

**Solutions**:

1. **Verify Network Policy Rules**
```bash
# Check if appropriate allow rules exist
oc describe networkpolicy allow-router-to-backend
oc describe networkpolicy allow-frontend-to-backend
```

2. **Test Without Network Policies**
```bash
# Temporarily delete network policies for testing
oc delete networkpolicy default-deny-all

# Test connectivity
# Re-create network policies after testing
oc apply -f k8s/base/networkpolicy.yaml
```

3. **Add Missing Allow Rules**
```bash
# Create additional network policy if needed
oc apply -f <new-network-policy>.yaml
```

---

## Authentication and Authorization Issues

### Issue: Google OAuth Not Working

**Symptoms**:
- Login page shows OAuth errors
- Google authentication fails
- Origin mismatch errors

**Diagnosis**:
```bash
# Check Google Client ID configuration
oc get configmap assetflow-config
oc describe configmap assetflow-config

# Check secret for Google Client Secret
oc describe secret assetflow-secrets
```

**Solutions**:

1. **Verify Google OAuth Configuration**
```bash
# Check Google Cloud Console settings
# - Verify Client ID matches
# - Verify authorized JavaScript origins
# - Verify authorized redirect URIs
```

2. **Update Configuration**
```bash
# Update ConfigMap with correct Client ID
oc edit configmap assetflow-config

# Update Secret with correct Client Secret
oc edit secret assetflow-secrets

# Restart pods to pick up changes
oc rollout restart deployment assetflow-backend
oc rollout restart deployment assetflow-frontend
```

3. **Verify Frontend Build**
```bash
# Check if Google Client ID is baked into frontend build
oc exec deployment/assetflow-frontend -- sh -c "grep -o 'GOOGLE_CLIENT_ID' /usr/share/nginx/html/static/js/main.*.js"

# If not found, rebuild frontend with correct build args
```

### Issue: JWT Token Issues

**Symptoms**:
- Authentication failures
- Token validation errors
- Unauthorized API responses

**Diagnosis**:
```bash
# Check JWT secret configuration
oc describe secret assetflow-secrets

# Check backend logs for JWT errors
oc logs -l app=assetflow-backend | grep -i jwt
```

**Solutions**:

1. **Verify JWT Secret**
```bash
# Ensure JWT_SECRET is set in secret
oc describe secret assetflow-secrets

# If missing, add it
oc edit secret assetflow-secrets
# Add: JWT_SECRET: <strong-random-secret>
```

2. **Restart Backend**
```bash
oc rollout restart deployment assetflow-backend
oc rollout status deployment assetflow-backend
```

### Issue: RBAC Permission Denied

**Symptoms**:
- Permission denied errors in logs
- Pods cannot access required resources
- Service account authorization failures

**Diagnosis**:
```bash
# Check service account
oc get serviceaccounts
oc describe serviceaccount assetflow-backend-sa

# Check roles and role bindings
oc get roles
oc get rolebindings
oc describe role assetflow-pod-reader
oc describe rolebinding assetflow-backend-binding
```

**Solutions**:

1. **Verify Role Permissions**
```bash
# Check if role has required permissions
oc describe role assetflow-pod-reader

# Add missing permissions if needed
oc edit role assetflow-pod-reader
```

2. **Verify Role Binding**
```bash
# Check if service account is bound to role
oc describe rolebinding assetflow-backend-binding

# Re-create role binding if needed
oc delete rolebinding assetflow-backend-binding
oc apply -f k8s/base/rbac.yaml
```

3. **Check Pod Service Account**
```bash
# Verify pod uses correct service account
oc describe pod <backend-pod> | grep -A 5 "ServiceAccount"

# Update deployment if wrong service account
oc edit deployment assetflow-backend
# Set: serviceAccountName: assetflow-backend-sa
```

---

## Storage and PVC Issues

### Issue: PVC Not Binding

**Symptoms**:
- PVC stuck in `Pending` state
- Pods cannot mount volumes
- Volume mount errors

**Diagnosis**:
```bash
# Check PVC status
oc get pvc
oc describe pvc assetflow-uploads-pvc

# Check storage classes
oc get storageclass
```

**Solutions**:

1. **Check Storage Class**
```bash
# Verify storage class exists
oc get storageclass

# Check PVC storage class
oc describe pvc assetflow-uploads-pvc | grep -A 5 "StorageClass"
```

2. **Check Available Storage**
```bash
# Check if cluster has available storage
oc describe nodes | grep -A 10 "Allocated resources"

# Check storage quotas
oc get resourcequota
oc describe resourcequota
```

3. **Recreate PVC**
```bash
# Delete and recreate PVC
oc delete pvc assetflow-uploads-pvc
oc apply -f k8s/base/pvc-uploads.yaml
```

### Issue: Multi-Attach Errors

**Symptoms**:
- Pods stuck in `ContainerCreating` state
- Multi-attach error in events
- Volume already in use by other pods

**Diagnosis**:
```bash
# Check pod events
oc describe pod <stuck-pod> | grep -i "attach"

# Check which pods are using the PVC
oc get pods -o wide
```

**Solutions**:

1. **Identify Conflicting Pods**
```bash
# Find pods using the same PVC
oc get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}'
```

2. **Delete Conflicting Pods**
```bash
# Delete old pods that are holding the volume
oc delete pod <old-pod-name>

# Let deployment recreate with correct configuration
```

3. **Use Single Replica for PVC**
```bash
# Ensure only one replica uses the PVC at a time
oc scale deployment assetflow-backend-storage-demo --replicas=1
```

### Issue: File Upload Not Persisting

**Symptoms**:
- Uploaded files disappear after pod restart
- Files not accessible across pod restarts
- Storage not working as expected

**Diagnosis**:
```bash
# Check if PVC is mounted
oc describe pod <storage-demo-pod> | grep -A 10 "Mounts"

# Check PVC status
oc get pvc
oc describe pvc assetflow-uploads-pvc
```

**Solutions**:

1. **Verify Volume Mount**
```bash
# Check deployment has volume mount
oc describe deployment assetflow-backend-storage-demo | grep -A 10 "volumeMounts"

# Edit deployment if missing
oc edit deployment assetflow-backend-storage-demo
```

2. **Test File Upload**
```bash
# Upload a test file
curl -X POST -F "file=@test.txt" https://assetflow-backend-.../uploads

# Verify file exists in pod
oc exec -it <storage-demo-pod> -- ls -la /app/uploads
```

3. **Test Persistence**
```bash
# Delete pod and recreate
oc delete pod <storage-demo-pod>

# Check if files persist in new pod
oc exec -it <new-storage-demo-pod> -- ls -la /app/uploads
```

---

## Performance and Scaling Issues

### Issue: HPA Not Scaling

**Symptoms**:
- HPA not increasing replica count
- CPU utilization high but no scaling
- Replica count stays at minimum

**Diagnosis**:
```bash
# Check HPA status
oc get hpa
oc describe hpa assetflow-backend-hpa

# Check current metrics
oc top pods
oc top nodes
```

**Solutions**:

1. **Verify Metrics Server**
```bash
# Check if metrics server is running
oc get pods -n openshift-monitoring | grep metrics

# Check if metrics are available
oc top pods
```

2. **Check HPA Configuration**
```bash
# Verify HPA target and thresholds
oc describe hpa assetflow-backend-hpa

# Adjust if needed
oc edit hpa assetflow-backend-hpa
```

3. **Generate Load**
```bash
# Generate load to trigger scaling
ab -n 1000 -c 10 https://assetflow-backend-.../healthz

# Watch HPA response
watch oc get hpa
```

4. **Check Resource Requests**
```bash
# Verify resource requests are set correctly
oc describe deployment assetflow-backend | grep -A 10 "Resources"

# HPA needs resource requests to calculate percentages
```

### Issue: Pods Not Scaling Down

**Symptoms**:
- HPA scales up but not down
- Replica count stays high after load decreases
- Resource waste

**Diagnosis**:
```bash
# Check HPA status
oc get hpa
oc describe hpa assetflow-backend-hpa

# Check current CPU utilization
oc top pods
```

**Solutions**:

1. **Check Stabilization Window**
```bash
# HPA has default stabilization window
# Wait 5 minutes after load decreases for scale-down
```

2. **Adjust HPA Configuration**
```bash
# Edit HPA to adjust scale-down behavior
oc edit hpa assetflow-backend-hpa

# Add stabilization window if needed
```

3. **Manual Scale Down**
```bash
# Force scale down if needed
oc scale deployment assetflow-backend --replicas=2
```

### Issue: High Memory Usage

**Symptoms**:
- Pods consuming excessive memory
- OOMKilled events
- Performance degradation

**Diagnosis**:
```bash
# Check memory usage
oc top pods
oc describe pod <high-memory-pod> | grep -i "oom"

# Check memory limits
oc describe deployment assetflow-backend | grep -A 10 "Resources"
```

**Solutions**:

1. **Increase Memory Limits**
```bash
# Edit deployment to increase memory limits
oc edit deployment assetflow-backend
# Increase memory limits in resources section
```

2. **Check for Memory Leaks**
```bash
# Monitor memory usage over time
watch oc top pods

# Check application logs for memory issues
oc logs -l app=assetflow-backend | grep -i memory
```

3. **Add Monitoring**
```bash
# Enable detailed memory monitoring
# Use OpenShift monitoring dashboards
```

---

## Monitoring and Logging Issues

### Issue: Logs Not Appearing

**Symptoms**:
- No logs visible in OpenShift console
- `oc logs` command returns no output
- Log aggregation not working

**Diagnosis**:
```bash
# Check if pods are running
oc get pods

# Try getting logs
oc logs <pod-name>
oc logs <pod-name> --previous
```

**Solutions**:

1. **Check Pod Status**
```bash
# Ensure pod is running
oc get pods
oc describe pod <pod-name>
```

2. **Check Logging Configuration**
```bash
# Verify application is writing logs
oc exec -it <pod-name> -- cat /proc/<pid>/fd/1

# Check application logging configuration
```

3. **Use Different Log Options**
```bash
# Get logs from all containers
oc logs <pod-name> --all-containers=true

# Get logs with timestamps
oc logs <pod-name> --timestamps=true
```

### Issue: Metrics Not Available

**Symptoms**:
- Metrics not showing in OpenShift console
- `oc top` command fails
- No CPU/memory data available

**Diagnosis**:
```bash
# Check metrics server
oc get pods -n openshift-monitoring | grep metrics

# Try top command
oc top pods
oc top nodes
```

**Solutions**:

1. **Check Metrics Server**
```bash
# Verify metrics server is running
oc get pods -n openshift-monitoring

# Restart metrics server if needed
oc delete pod -n openshift-monitoring <metrics-pod>
```

2. **Check Resource Requests**
```bash
# Metrics server needs resource requests
oc describe deployment assetflow-backend | grep -A 10 "Resources"
```

3. **Use Alternative Monitoring**
```bash
# Use OpenShift monitoring dashboards
# Navigate to Observe → Metrics in console
```

---

## Security Issues

### Issue: TLS Certificate Errors

**Symptoms**:
- Browser certificate warnings
- SSL handshake failures
- Mixed content errors

**Diagnosis**:
```bash
# Check route TLS configuration
oc describe route assetflow-frontend | grep -A 10 "TLS"

# Test with curl
curl -k https://assetflow-frontend-.../
```

**Solutions**:

1. **Verify TLS Configuration**
```bash
# Check route uses edge termination
oc describe route assetflow-frontend

# Ensure termination: edge
```

2. **Clear Browser Cache**
```bash
# Clear SSL cache in browser
# Try in incognito mode
```

3. **Check Certificate Validity**
```bash
# Use browser developer tools to check certificate
# Verify certificate is not expired
```

### Issue: Network Policy Blocking Legitimate Traffic

**Symptoms**:
- Legitimate traffic blocked
- Connection timeouts
- Network policy denied events

**Diagnosis**:
```bash
# Check network policies
oc get networkpolicy
oc describe networkpolicy default-deny-all

# Check pod events
oc describe pod <affected-pod> | grep -i network
```

**Solutions**:

1. **Review Network Policy Rules**
```bash
# Check if appropriate allow rules exist
oc describe networkpolicy allow-router-to-backend
oc describe networkpolicy allow-frontend-to-backend
```

2. **Add Missing Allow Rules**
```bash
# Create additional network policy
oc apply -f <new-policy>.yaml
```

3. **Test Without Network Policies**
```bash
# Temporarily disable for testing
oc delete networkpolicy default-deny-all

# Re-enable after testing
oc apply -f k8s/base/networkpolicy.yaml
```

---

## CI/CD Pipeline Issues

### Issue: GitHub Actions Failing

**Symptoms**:
- Workflow runs failing
- Build errors in GitHub Actions
- Deployment steps failing

**Diagnosis**:
```bash
# Check workflow status in GitHub
# Navigate to Actions tab in repository
# Check workflow run logs
```

**Solutions**:

1. **Check GitHub Secrets**
```bash
# Verify required secrets are set
# GHCR_TOKEN, OPENSHIFT_SERVER, OPENSHIFT_TOKEN, OPENSHIFT_NAMESPACE
# Navigate to Repository → Settings → Secrets
```

2. **Check Workflow Configuration**
```bash
# Verify workflow YAML syntax
cat .github/workflows/ci-cd.yaml

# Check for indentation errors
```

3. **Test Locally**
```bash
# Test build locally
docker build -t test ./backend
docker build -t test ./frontend
```

4. **Check OpenShift Login**
```bash
# Verify OpenShift credentials are valid
oc login --server=<server> --token=<token>
```

### Issue: Docker Build Failures

**Symptoms**:
- Docker build failing in CI/CD
- Dependency installation errors
- Build context issues

**Diagnosis**:
```bash
# Test build locally
docker build -t test ./backend
docker build -t test ./frontend
```

**Solutions**:

1. **Check Dockerfile Syntax**
```bash
# Verify Dockerfile syntax
cat backend/Dockerfile
cat frontend/Dockerfile
```

2. **Check Dependencies**
```bash
# Verify requirements.txt is valid
cat backend/requirements.txt

# Verify package.json is valid
cat frontend/package.json
```

3. **Check Build Context**
```bash
# Verify .dockerignore is not excluding needed files
cat backend/.dockerignore
cat frontend/.dockerignore
```

---

## Frontend Issues

### Issue: Blank Login Page

**Symptoms**:
- Frontend loads but shows blank page
- JavaScript errors in console
- No UI elements visible

**Diagnosis**:
```bash
# Check frontend pod status
oc get pods -l app=assetflow-frontend

# Check frontend logs
oc logs -l app=assetflow-frontend

# Check browser console for errors
```

**Solutions**:

1. **Check Environment Variables**
```bash
# Verify environment variables are baked in
oc exec deployment/assetflow-frontend -- sh -c "grep -o 'REACT_APP_BACKEND_URL' /usr/share/nginx/html/static/js/main.*.js"
oc exec deployment/assetflow-frontend -- sh -c "grep -o 'REACT_APP_GOOGLE_CLIENT_ID' /usr/share/nginx/html/static/js/main.*.js"
```

2. **Rebuild Frontend**
```bash
# Rebuild with correct build arguments
# Update GitHub Actions workflow
# Trigger new build
```

3. **Check Browser Console**
```bash
# Open browser developer tools
# Check Console tab for JavaScript errors
# Check Network tab for failed requests
```

### Issue: API Calls Failing

**Symptoms**:
- Frontend cannot connect to backend
- CORS errors in browser console
- Network timeout errors

**Diagnosis**:
```bash
# Check backend URL configuration
oc get configmap assetflow-config
oc describe configmap assetflow-config

# Check CORS configuration
oc describe configmap assetflow-config | grep CORS
```

**Solutions**:

1. **Verify Backend URL**
```bash
# Ensure REACT_APP_BACKEND_URL is correct
# Should be production route URL, not internal service name
```

2. **Check CORS Configuration**
```bash
# Verify CORS_ORIGINS includes frontend route
oc describe configmap assetflow-config

# Update if needed
oc edit configmap assetflow-config
```

3. **Test Backend Connectivity**
```bash
# Test backend from browser
curl https://assetflow-backend-.../healthz
```

---

## Serverless Function Issues

### Issue: Knative Service Not Starting

**Symptoms**:
- Knative service stuck in not ready state
- Pods not created for service
- Service shows 0/0 ready

**Diagnosis**:
```bash
# Check Knative service status
oc get ksvc
oc describe ksvc assetflow-reminder-service

# Check Knative pods
oc get pods -l serving.knative.dev/service=assetflow-reminder-service
```

**Solutions**:

1. **Check Service Configuration**
```bash
# Verify service configuration
oc describe ksvc assetflow-reminder-service

# Check image reference
oc get ksvc assetflow-reminder-service -o jsonpath='{.spec.template.spec.containers[0].image}'
```

2. **Check Knative Installation**
```bash
# Verify Knative is installed
oc get pods -n knative-serving
oc get pods -n knative-eventing
```

3. **Recreate Service**
```bash
# Delete and recreate service
oc delete ksvc assetflow-reminder-service
oc apply -f k8s/base/knative-reminder-service.yaml
```

### Issue: PingSource Not Triggering

**Symptoms**:
- PingSource not triggering function
- No events generated
- Cron schedule not working

**Diagnosis**:
```bash
# Check PingSource status
oc get pingsources
oc describe pingsource assetflow-reminder-ping

# Check event logs
oc logs -l serving.knative.dev/service=assetflow-reminder-service
```

**Solutions**:

1. **Verify PingSource Configuration**
```bash
# Check schedule format
oc describe pingsource assetflow-reminder-ping

# Verify sink reference
oc describe pingsource assetflow-reminder-ping | grep -A 5 "Sink"
```

2. **Check Schedule Format**
```bash
# Ensure cron schedule is valid
# Format: "*/5 * * * *" for every 5 minutes
```

3. **Test Manual Trigger**
```bash
# Create test event to verify service works
oc apply -f <test-event>.yaml
```

---

## General Troubleshooting Commands

### System Status
```bash
# Overall system status
oc get all
oc get pods
oc get nodes
oc top pods
oc top nodes
```

### Debugging
```bash
# Describe resources
oc describe pod <pod-name>
oc describe deployment <deployment-name>
oc describe service <service-name>
oc describe route <route-name>

# View logs
oc logs <pod-name>
oc logs <pod-name> --previous
oc logs -f <pod-name>
oc logs -l app=assetflow-backend
```

### Events
```bash
# View recent events
oc get events --sort-by='.lastTimestamp'
oc get events --field-selector involvedObject.name=<pod-name>
```

### Resource Management
```bash
# Scale resources
oc scale deployment assetflow-backend --replicas=4
oc scale deployment assetflow-frontend --replicas=3

# Restart deployments
oc rollout restart deployment assetflow-backend
oc rollout status deployment assetflow-backend
```

### Network Debugging
```bash
# Test connectivity
oc run test-pod --image=curlimages/curl -i --rm --restart=Never -- curl http://assetflow-backend:8000/healthz

# Check DNS
oc exec -it <pod-name> -- nslookup assetflow-backend
```

---

## Emergency Procedures

### Full System Restart
```bash
# Restart all deployments
oc rollout restart deployment assetflow-backend
oc rollout restart deployment assetflow-frontend
oc rollout restart deployment assetflow-backend-storage-demo

# Wait for rollouts to complete
oc rollout status deployment assetflow-backend
oc rollout status deployment assetflow-frontend
```

### Rollback to Previous Version
```bash
# Check rollout history
oc rollout history deployment assetflow-backend

# Rollback to previous version
oc rollout undo deployment assetflow-backend

# Rollback to specific version
oc rollout undo deployment assetflow-backend --to-revision=<revision-number>
```

### Clean Slate Redeployment
```bash
# Delete all resources
oc delete all -l app=assetflow-backend
oc delete all -l app=assetflow-frontend

# Reapply manifests
oc apply -f k8s/base/

# Verify deployment
oc get pods
oc get all
```

---

## Contact and Support

### Internal Resources
- VERIFICATION_CHECKLIST.md - Detailed verification procedures
- DEMO_SCRIPT.md - Live demonstration procedures
- MONITORING_GUIDE.md - Monitoring setup and usage
- TEST_SCENARIOS.md - Testing procedures

### External Resources
- OpenShift Documentation: https://docs.openshift.com/
- Kubernetes Documentation: https://kubernetes.io/docs/
- GitHub Actions Documentation: https://docs.github.com/en/actions

### Emergency Contacts
- OpenShift Cluster Administrator
- GitHub Repository Maintainer
- DevOps Team Lead

---

## Conclusion

This troubleshooting guide covers the most common issues that may occur during deployment, operation, or demonstration of the AssetFlow application on OpenShift. Follow the diagnostic steps systematically, and use the provided solutions to resolve issues efficiently.

For issues not covered in this guide, refer to the official OpenShift and Kubernetes documentation, or contact your system administrator for assistance.