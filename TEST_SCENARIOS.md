# AssetFlow OpenShift - Test Scenarios

## Overview

This document provides comprehensive test scenarios for validating all 12 hackathon deliverables of the AssetFlow application on Red Hat OpenShift. Each scenario includes detailed procedures, expected outcomes, and verification steps.

## Table of Contents

1. [Deliverable 1: Git Repository Testing](#deliverable-1-git-repository-testing)
2. [Deliverable 2: CI/CD Pipeline Testing](#deliverable-2-cicd-pipeline-testing)
3. [Deliverable 3: Kubernetes/OpenShift Manifests Testing](#deliverable-3-kubernetesopenshift-manifests-testing)
4. [Deliverable 4: Container Registry Testing](#deliverable-4-container-registry-testing)
5. [Deliverable 5: Serverless Function Testing](#deliverable-5-serverless-function-testing)
6. [Deliverable 6: Load Balancing Testing](#deliverable-6-load-balancing-testing)
7. [Deliverable 7: Horizontal Pod Autoscaling Testing](#deliverable-7-horizontal-pod-autoscaling-testing)
8. [Deliverable 8: High Availability Testing](#deliverable-8-high-availability-testing)
9. [Deliverable 9: Security Testing](#deliverable-9-security-testing)
10. [Deliverable 10: Health Probes Testing](#deliverable-10-health-probes-testing)
11. [Deliverable 11: Persistent Storage Testing](#deliverable-11-persistent-storage-testing)
12. [Deliverable 12: Monitoring and Logging Testing](#deliverable-12-monitoring-and-logging-testing)

---

## Deliverable 1: Git Repository Testing

### Test Scenario 1.1: Repository Structure Verification

**Objective**: Verify repository contains all required components with proper structure

**Prerequisites**:
- Git repository access
- Read permissions on repository

**Test Steps**:
1. Clone repository: `git clone https://github.com/ayshrosine/red_hat_assets.git`
2. Navigate to repository: `cd red_hat_assets`
3. List all files: `git ls-files`
4. Verify directory structure: `ls -la`

**Expected Outcomes**:
- Backend directory exists with source files
- Frontend directory exists with source files
- k8s/base/ directory exists with YAML manifests
- .github/workflows/ directory exists with CI/CD configuration
- Documentation files exist (README.md, deployment guides)

**Verification Commands**:
```bash
# Check directory structure
find . -type d -maxdepth 2
git ls-files | head -20

# Verify key files exist
test -f backend/server.py && echo "Backend server exists"
test -f frontend/src/App.js && echo "Frontend App exists"
test -f k8s/base/backend-deployment.yaml && echo "Backend deployment exists"
test -f .github/workflows/ci-cd.yaml && echo "CI/CD workflow exists"
```

**Success Criteria**:
- ✅ All required directories present
- ✅ All key files exist
- ✅ Structure matches project requirements

---

### Test Scenario 1.2: Security Best Practices Verification

**Objective**: Verify repository follows security best practices

**Prerequisites**:
- Git repository access
- Basic understanding of Git security

**Test Steps**:
1. Check .gitignore configuration: `cat .gitignore`
2. Search for sensitive data: `git grep -i "password\|secret\|token" -- '*.yaml' '*.py' '*.js'`
3. Verify secret templates use placeholders: `cat k8s/base/secret-template.yaml`
4. Check for committed credentials: `git log --all --full-history --source -- "*token.json*"`

**Expected Outcomes**:
- .gitignore excludes sensitive files (.env, credentials, etc.)
- No hardcoded credentials in source code
- Secret templates use placeholders
- No committed credential files

**Verification Commands**:
```bash
# Check .gitignore
cat .gitignore | grep -E "(env|credentials|token|secret)"

# Search for sensitive data patterns
git grep -i "password\|secret\|api_key\|private_key" -- '*.yaml' '*.py' '*.js' || echo "No sensitive data found"

# Verify secret template
cat k8s/base/secret-template.yaml | grep "<from"
```

**Success Criteria**:
- ✅ Proper .gitignore configuration
- ✅ No hardcoded credentials
- ✅ Secret templates use placeholders
- ✅ No committed sensitive files

---

## Deliverable 2: CI/CD Pipeline Testing

### Test Scenario 2.1: CI/CD Workflow Verification

**Objective**: Verify GitHub Actions workflow is properly configured

**Prerequisites**:
- GitHub repository access
- GitHub Actions enabled

**Test Steps**:
1. Navigate to GitHub repository
2. Click on "Actions" tab
3. View workflow runs
4. Examine workflow configuration

**Expected Outcomes**:
- CI/CD workflow defined
- Workflow triggers on push to main
- Build, test, and deploy stages configured
- No syntax errors in workflow YAML

**Verification Commands**:
```bash
# View workflow configuration
cat .github/workflows/ci-cd.yaml

# Check workflow syntax (requires GitHub CLI)
gh workflow view ci-cd
```

**Success Criteria**:
- ✅ Workflow properly configured
- ✅ No syntax errors
- ✅ All stages defined
- ✅ Proper triggers configured

---

### Test Scenario 2.2: Automated Build Testing

**Objective**: Verify automated build process works correctly

**Prerequisites**:
- GitHub repository access
- Ability to trigger workflow

**Test Steps**:
1. Create a test commit: `git commit --allow-empty -m "Test build"`
2. Push to main branch: `git push origin main`
3. Monitor workflow execution in GitHub Actions
4. Verify build completes successfully

**Expected Outcomes**:
- Workflow triggers automatically
- Backend image builds successfully
- Frontend image builds successfully
- Images pushed to GHCR

**Verification Commands**:
```bash
# Monitor workflow (requires GitHub CLI)
gh workflow list
gh run list --workflow=ci-cd.yaml
gh run view <run-id>

# Verify images in registry
docker pull ghcr.io/ayshrosine/assetflow-backend:latest
docker pull ghcr.io/ayshrosine/assetflow-frontend:latest
```

**Success Criteria**:
- ✅ Workflow triggers automatically
- ✅ Build completes successfully
- ✅ Images pushed to registry
- ✅ No build errors

---

### Test Scenario 2.3: Automated Deployment Testing

**Objective**: Verify automated deployment to OpenShift works

**Prerequisites**:
- Successful CI/CD build
- OpenShift cluster access
- GitHub secrets configured

**Test Steps**:
1. Trigger workflow (push to main)
2. Monitor deploy stage in GitHub Actions
3. Verify deployment updates in OpenShift
4. Check rollout status

**Expected Outcomes**:
- Workflow authenticates to OpenShift
- Deployment images updated
- Rollout completes successfully
- New pods running

**Verification Commands**:
```bash
# Monitor deployment status
oc get pods
oc get deployment assetflow-backend
oc get deployment assetflow-frontend

# Check rollout status
oc rollout status deployment/assetflow-backend
oc rollout status deployment/assetflow-frontend

# Verify new pods
oc describe pod <new-pod-name>
```

**Success Criteria**:
- ✅ Deployment completes successfully
- ✅ New pods running
- ✅ Rollout status healthy
- ✅ No deployment errors

---

## Deliverable 3: Kubernetes/OpenShift Manifests Testing

### Test Scenario 3.1: Manifest Application Testing

**Objective**: Verify all Kubernetes manifests can be applied successfully

**Prerequisites**:
- OpenShift cluster access
- oc CLI configured
- Namespace access

**Test Steps**:
1. Apply all manifests: `oc apply -f k8s/base/`
2. Verify resource creation: `oc get all`
3. Check for errors: `oc get events --sort-by='.lastTimestamp'`

**Expected Outcomes**:
- All resources created successfully
- No error events
- Resources in expected state

**Verification Commands**:
```bash
# Apply manifests
oc apply -f k8s/base/

# Verify resource creation
oc get all
oc get configmaps
oc get secrets
oc get pvc
oc get networkpolicy
oc get hpa
oc get poddisruptionbudget

# Check for errors
oc get events --sort-by='.lastTimestamp' | grep -i error
```

**Success Criteria**:
- ✅ All manifests apply successfully
- ✅ No error events
- ✅ Resources in expected state
- ✅ No validation errors

---

### Test Scenario 3.2: Resource Configuration Verification

**Objective**: Verify Kubernetes resources are properly configured

**Prerequisites**:
- Manifests applied
- Resources created

**Test Steps**:
1. Verify deployment configurations: `oc describe deployment assetflow-backend`
2. Verify service configurations: `oc describe service assetflow-backend`
3. Verify route configurations: `oc describe route assetflow-frontend`
4. Verify HPA configuration: `oc describe hpa assetflow-backend-hpa`

**Expected Outcomes**:
- Deployments have correct replica counts
- Services have correct selectors
- Routes have correct TLS configuration
- HPA has correct targets

**Verification Commands**:
```bash
# Check deployment configuration
oc describe deployment assetflow-backend | grep -A 5 "Replicas"
oc describe deployment assetflow-backend | grep -A 10 "Resources"

# Check service configuration
oc describe service assetflow-backend | grep -A 5 "Selector"
oc describe service assetflow-backend | grep -A 5 "Port"

# Check route configuration
oc describe route assetflow-frontend | grep -A 5 "TLS"
oc describe route assetflow-frontend | grep -A 5 "Host"

# Check HPA configuration
oc describe hpa assetflow-backend-hpa | grep -A 10 "Metrics"
```

**Success Criteria**:
- ✅ Deployments configured correctly
- ✅ Services configured correctly
- ✅ Routes configured correctly
- ✅ HPA configured correctly

---

## Deliverable 4: Container Registry Testing

### Test Scenario 4.1: Image Pull Testing

**Objective**: Verify container images can be pulled from registry

**Prerequisites**:
- Docker installed
- Registry access
- Authentication configured

**Test Steps**:
1. Pull backend image: `docker pull ghcr.io/ayshrosine/assetflow-backend:latest`
2. Pull frontend image: `docker pull ghcr.io/ayshrosine/assetflow-frontend:latest`
3. Verify image integrity: `docker inspect ghcr.io/ayshrosine/assetflow-backend:latest`

**Expected Outcomes**:
- Images pull successfully
- No authentication errors
- Images are valid and not corrupted

**Verification Commands**:
```bash
# Pull images
docker pull ghcr.io/ayshrosine/assetflow-backend:latest
docker pull ghcr.io/ayshrosine/assetflow-frontend:latest

# Verify images
docker images | grep assetflow
docker inspect ghcr.io/ayshrosine/assetflow-backend:latest
docker inspect ghcr.io/ayshrosine/assetflow-frontend:latest
```

**Success Criteria**:
- ✅ Images pull successfully
- ✅ No authentication errors
- ✅ Images are valid
- ✅ Image metadata correct

---

### Test Scenario 4.2: OpenShift Image Pull Testing

**Objective**: Verify OpenShift can pull images from registry

**Prerequisites**:
- OpenShift cluster access
- Image pull secrets configured

**Test Steps**:
1. Check pod status: `oc get pods`
2. Describe pod to check image pull: `oc describe pod <pod-name>`
3. Verify image reference: `oc get deployment assetflow-backend -o jsonpath='{.spec.template.spec.containers[0].image}'`

**Expected Outcomes**:
- Pods start successfully
- No ImagePullBackOff errors
- Correct image references

**Verification Commands**:
```bash
# Check pod status
oc get pods

# Check for image pull errors
oc describe pod <pod-name> | grep -i "image"

# Verify image references
oc get deployment assetflow-backend -o jsonpath='{.spec.template.spec.containers[0].image}'
oc get deployment assetflow-frontend -o jsonpath='{.spec.template.spec.containers[0].image}'
```

**Success Criteria**:
- ✅ Pods start successfully
- ✅ No image pull errors
- ✅ Correct image references
- ✅ Images are up-to-date

---

## Deliverable 5: Serverless Function Testing

### Test Scenario 5.1: Knative Service Verification

**Objective**: Verify Knative service is running and accessible

**Prerequisites**:
- Knative installed
- Service deployed

**Test Steps**:
1. Check Knative service status: `oc get ksvc`
2. Describe service: `oc describe ksvc assetflow-reminder-service`
3. Check service pods: `oc get pods -l serving.knative.dev/service=assetflow-reminder-service`

**Expected Outcomes**:
- Knative service is ready
- Service URL is accessible
- Pods are running

**Verification Commands**:
```bash
# Check Knative service
oc get ksvc
oc describe ksvc assetflow-reminder-service

# Check service pods
oc get pods -l serving.knative.dev/service=assetflow-reminder-service

# Test service URL
SERVICE_URL=$(oc get ksvc assetflow-reminder-service -o jsonpath='{.status.url}')
curl $SERVICE_URL
```

**Success Criteria**:
- ✅ Knative service ready
- ✅ Service URL accessible
- ✅ Pods running
- ✅ No service errors

---

### Test Scenario 5.2: PingSource Trigger Testing

**Objective**: Verify PingSource triggers serverless function

**Prerequisites**:
- Knative service running
- PingSource configured

**Test Steps**:
1. Check PingSource status: `oc get pingsources`
2. Describe PingSource: `oc describe pingsource assetflow-reminder-ping`
3. Monitor function logs: `oc logs -l serving.knative.dev/service=assetflow-reminder-service`

**Expected Outcomes**:
- PingSource is ready
- Triggers are firing
- Function executes on schedule

**Verification Commands**:
```bash
# Check PingSource
oc get pingsources
oc describe pingsource assetflow-reminder-ping

# Monitor function logs
oc logs -l serving.knative.dev/service=assetflow-reminder-service --tail=50

# Wait for trigger (based on schedule)
sleep 300  # Wait 5 minutes for cron trigger
oc logs -l serving.knative.dev/service=assetflow-reminder-service --tail=10
```

**Success Criteria**:
- ✅ PingSource ready
- ✅ Triggers firing
- ✅ Function executes
- ✅ Logs show execution

---

## Deliverable 6: Load Balancing Testing

### Test Scenario 6.1: Service Endpoint Verification

**Objective**: Verify service endpoints are distributed across pods

**Prerequisites**:
- Multiple pods running
- Service configured

**Test Steps**:
1. Check service endpoints: `oc get endpoints assetflow-backend`
2. Verify multiple endpoints exist
3. Test load distribution

**Expected Outcomes**:
- Service has multiple endpoints
- Endpoints correspond to running pods
- Load is distributed

**Verification Commands**:
```bash
# Check service endpoints
oc get endpoints assetflow-backend
oc get endpoints assetflow-frontend

# Verify pod IPs match endpoints
oc get pods -l app=assetflow-backend -o wide

# Test load distribution
for i in {1..10}; do
  curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz
  echo "--- Request $i ---"
done
```

**Success Criteria**:
- ✅ Multiple endpoints exist
- ✅ Endpoints match pod IPs
- ✅ Load distributed
- ✅ No endpoint errors

---

### Test Scenario 6.2: Load Distribution Testing

**Objective**: Verify requests are distributed across multiple pods

**Prerequisites**:
- Multiple backend pods running
- Load testing tool available

**Test Steps**:
1. Generate load: `ab -n 100 -c 10 https://assetflow-backend-.../healthz`
2. Monitor pod logs during load
3. Verify requests distributed

**Expected Outcomes**:
- Requests distributed across pods
- No single pod overloaded
- All pods handle requests

**Verification Commands**:
```bash
# Generate load
ab -n 100 -c 10 https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz

# Monitor pod logs during load
oc logs -l app=assetflow-backend --tail=20 --follow=true

# Check pod request counts
oc logs -l app=assetflow-backend | grep "GET /healthz" | wc -l
```

**Success Criteria**:
- ✅ Requests distributed
- ✅ No pod overload
- ✅ All pods handle requests
- ✅ Balanced distribution

---

## Deliverable 7: Horizontal Pod Autoscaling Testing

### Test Scenario 7.1: HPA Configuration Verification

**Objective**: Verify HPA is properly configured

**Prerequisites**:
- HPA deployed
- Metrics server available

**Test Steps**:
1. Check HPA status: `oc get hpa`
2. Describe HPA: `oc describe hpa assetflow-backend-hpa`
3. Verify metrics server: `oc top pods`

**Expected Outcomes**:
- HPA is ready
- Target utilization configured
- Metrics available

**Verification Commands**:
```bash
# Check HPA
oc get hpa
oc describe hpa assetflow-backend-hpa

# Verify metrics available
oc top pods
oc top nodes

# Check HPA metrics
oc get hpa assetflow-backend-hpa -o yaml
```

**Success Criteria**:
- ✅ HPA ready
- ✅ Targets configured
- ✅ Metrics available
- ✅ No HPA errors

---

### Test Scenario 7.2: Autoscaling Behavior Testing

**Objective**: Verify HPA scales pods based on CPU utilization

**Prerequisites**:
- HPA configured
- Load testing tool available

**Test Steps**:
1. Note current replica count: `oc get hpa`
2. Generate load: `ab -n 1000 -c 20 https://assetflow-backend-.../healthz`
3. Monitor HPA behavior: `watch oc get hpa`
4. Monitor pod creation: `watch oc get pods`

**Expected Outcomes**:
- HPA detects increased CPU
- Replica count increases
- New pods start successfully
- Scale-down after load decreases

**Verification Commands**:
```bash
# Note initial state
oc get hpa
oc get pods

# Generate load
ab -n 1000 -c 20 https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz

# Monitor HPA behavior
watch oc get hpa
watch oc get pods

# Wait for scale-down (5+ minutes)
sleep 300
oc get hpa
oc get pods
```

**Success Criteria**:
- ✅ HPA detects load increase
- ✅ Replica count increases
- ✅ New pods start successfully
- ✅ Scale-down after load decreases

---

## Deliverable 8: High Availability Testing

### Test Scenario 8.1: Replica Configuration Verification

**Objective**: Verify multiple replicas are configured

**Prerequisites**:
- Deployments configured

**Test Steps**:
1. Check deployment replicas: `oc get deployment assetflow-backend`
2. Verify running pods: `oc get pods -l app=assetflow-backend`
3. Check pod distribution: `oc get pods -l app=assetflow-backend -o wide`

**Expected Outcomes**:
- Multiple replicas configured
- Multiple pods running
- Pods distributed across nodes

**Verification Commands**:
```bash
# Check deployment configuration
oc get deployment assetflow-backend
oc describe deployment assetflow-backend | grep -A 5 "Replicas"

# Check running pods
oc get pods -l app=assetflow-backend
oc get pods -l app=assetflow-frontend

# Check pod distribution
oc get pods -l app=assetflow-backend -o wide
```

**Success Criteria**:
- ✅ Multiple replicas configured
- ✅ Multiple pods running
- ✅ Pods distributed
- ✅ All pods healthy

---

### Test Scenario 8.2: Rolling Update Testing

**Objective**: Verify rolling updates provide zero downtime

**Prerequisites**:
- Application running
- Load testing tool available

**Test Steps**:
1. Start continuous health checks: `while true; do curl https://assetflow-backend-.../healthz; sleep 1; done`
2. Trigger rolling update: `oc set image deployment/assetflow-backend backend=ghcr.io/ayshrosine/assetflow-backend:latest`
3. Monitor rollout: `oc rollout status deployment/assetflow-backend`
4. Verify continuous service during update

**Expected Outcomes**:
- No downtime during update
- Old pods gradually terminated
- New pods gradually started
- Health checks continue to succeed

**Verification Commands**:
```bash
# Start continuous health checks (in separate terminal)
while true; do
  curl -s https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz
  echo "Check at $(date)"
  sleep 1
done

# Trigger rolling update
oc set image deployment/assetflow-backend backend=ghcr.io/ayshrosine/assetflow-backend:latest

# Monitor rollout
oc rollout status deployment/assetflow-backend

# Check pod transitions
watch oc get pods
```

**Success Criteria**:
- ✅ No downtime during update
- ✅ Gradual pod transition
- ✅ Health checks succeed throughout
- ✅ Rollout completes successfully

---

### Test Scenario 8.3: Pod Disruption Budget Testing

**Objective**: Verify PDB maintains minimum available pods

**Prerequisites**:
- PDB configured
- Multiple pods running

**Test Steps**:
1. Check PDB status: `oc get pdb`
2. Describe PDB: `oc describe pdb assetflow-backend-pdb`
3. Try to evict pod: `oc delete pod <pod-name>`
4. Verify minimum pods maintained

**Expected Outcomes**:
- PDB allows voluntary disruptions
- Minimum pods maintained
- New pods created if needed

**Verification Commands**:
```bash
# Check PDB
oc get pdb
oc describe pdb assetflow-backend-pdb

# Try pod deletion
oc get pods -l app=assetflow-backend
oc delete pod <backend-pod-name>

# Verify minimum maintained
oc get pods -l app=assetflow-backend
oc describe pdb assetflow-backend-pdb
```

**Success Criteria**:
- ✅ PDB configured correctly
- ✅ Minimum pods maintained
- ✅ Disruptions controlled
- ✅ No availability loss

---

## Deliverable 9: Security Testing

### Test Scenario 9.1: TLS/SSL Verification

**Objective**: Verify HTTPS/TLS is properly configured

**Prerequisites**:
- Routes configured
- TLS certificates valid

**Test Steps**:
1. Check route TLS configuration: `oc describe route assetflow-frontend`
2. Test HTTPS access: `curl -k https://assetflow-frontend-.../`
3. Verify certificate in browser

**Expected Outcomes**:
- Routes use TLS edge termination
- HTTPS accessible
- Certificates valid

**Verification Commands**:
```bash
# Check route TLS
oc describe route assetflow-frontend | grep -A 10 "TLS"
oc describe route assetflow-backend | grep -A 10 "TLS"

# Test HTTPS access
curl -k https://assetflow-frontend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/
curl -k https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz

# Check certificate (in browser)
# Navigate to route URL and check certificate
```

**Success Criteria**:
- ✅ TLS configured
- ✅ HTTPS accessible
- ✅ Certificates valid
- ✅ No SSL errors

---

### Test Scenario 9.2: Secrets Management Verification

**Objective**: Verify secrets are properly managed

**Prerequisites**:
- Secrets configured
- No sensitive data in source

**Test Steps**:
1. List secrets: `oc get secrets`
2. Describe secret: `oc describe secret assetflow-secrets`
3. Verify no secrets in source code

**Expected Outcomes**:
- Secrets exist in cluster
- No sensitive data in source
- Secrets properly mounted

**Verification Commands**:
```bash
# Check secrets
oc get secrets
oc describe secret assetflow-secrets

# Verify secrets not in source
git grep -i "password\|secret" -- '*.yaml' '*.py' '*.js' || echo "No secrets in source"

# Verify secret mounting
oc describe pod <backend-pod> | grep -A 20 "Environment"
```

**Success Criteria**:
- ✅ Secrets configured
- ✅ No secrets in source
- ✅ Secrets properly mounted
- ✅ Access controlled

---

### Test Scenario 9.3: RBAC Verification

**Objective**: Verify RBAC provides least-privilege access

**Prerequisites**:
- RBAC configured
- Service accounts created

**Test Steps**:
1. Check service accounts: `oc get serviceaccounts`
2. Check roles: `oc get roles`
3. Check role bindings: `oc get rolebindings`
4. Verify pod uses service account

**Expected Outcomes**:
- Service accounts exist
- Roles have minimal permissions
- Bindings correctly configured
- Pods use service accounts

**Verification Commands**:
```bash
# Check RBAC resources
oc get serviceaccounts
oc get roles
oc get rolebindings

# Describe role permissions
oc describe role assetflow-pod-reader

# Verify pod service account
oc describe pod <backend-pod> | grep -A 5 "ServiceAccount"
```

**Success Criteria**:
- ✅ Service accounts configured
- ✅ Minimal permissions
- ✅ Bindings correct
- ✅ Pods use service accounts

---

### Test Scenario 9.4: Network Policy Verification

**Objective**: Verify network policies control traffic correctly

**Prerequisites**:
- Network policies configured
- Policies applied

**Test Steps**:
1. List network policies: `oc get networkpolicy`
2. Describe policies: `oc describe networkpolicy default-deny-all`
3. Test allowed traffic
4. Test denied traffic

**Expected Outcomes**:
- Default-deny policy exists
- Explicit allow rules work
- Unwanted traffic blocked

**Verification Commands**:
```bash
# Check network policies
oc get networkpolicy
oc describe networkpolicy default-deny-all
oc describe networkpolicy allow-router-to-backend

# Test allowed traffic
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz

# Check for denied traffic in pod events
oc describe pod <pod-name> | grep -i network
```

**Success Criteria**:
- ✅ Default-deny configured
- ✅ Allow rules work
- ✅ Unwanted traffic blocked
- ✅ No policy errors

---

## Deliverable 10: Health Probes Testing

### Test Scenario 10.1: Health Endpoint Verification

**Objective**: Verify health endpoints are accessible and return correct responses

**Prerequisites**:
- Backend pods running
- Endpoints configured

**Test Steps**:
1. Test liveness endpoint: `curl https://assetflow-backend-.../healthz`
2. Test readiness endpoint: `curl https://assetflow-backend-.../readyz`
3. Test startup endpoint: `curl https://assetflow-backend-.../startupz`

**Expected Outcomes**:
- All endpoints return 200 OK
- Endpoints return correct JSON
- Endpoints respond quickly

**Verification Commands**:
```bash
# Test health endpoints
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/readyz
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/startupz

# Test from within cluster
oc run test-pod --image=curlimages/curl -i --rm --restart=Never -- curl http://assetflow-backend:8000/healthz
```

**Success Criteria**:
- ✅ All endpoints return 200
- ✅ Correct JSON responses
- ✅ Fast response times
- ✅ No endpoint errors

---

### Test Scenario 10.2: Probe Configuration Verification

**Objective**: Verify health probes are correctly configured

**Prerequisites**:
- Deployments configured
- Probes defined

**Test Steps**:
1. Check probe configuration: `oc describe deployment assetflow-backend`
2. Verify probe settings
3. Test probe behavior

**Expected Outcomes**:
- Probes configured with correct settings
- Appropriate intervals and thresholds
- Probes working as expected

**Verification Commands**:
```bash
# Check probe configuration
oc describe deployment assetflow-backend | grep -A 20 "Probe"

# Verify probe settings
oc describe deployment assetflow-backend | grep -A 5 "livenessProbe"
oc describe deployment assetflow-backend | grep -A 5 "readinessProbe"
oc describe deployment assetflow-backend | grep -A 5 "startupProbe"

# Monitor probe status
oc describe pod <backend-pod> | grep -A 10 "Probe"
```

**Success Criteria**:
- ✅ Probes configured correctly
- ✅ Appropriate settings
- ✅ Probes working
- ✅ No probe failures

---

### Test Scenario 10.3: Probe Failure Testing

**Objective**: Verify probes detect failures and trigger appropriate actions

**Prerequisites**:
- Application running
- Ability to break health endpoints

**Test Steps**:
1. Monitor pod restart count: `oc get pods`
2. Break liveness endpoint (simulate failure)
3. Monitor pod restart
4. Verify readiness probe affects traffic

**Expected Outcomes**:
- Liveness probe failure triggers restart
- Readiness probe failure stops traffic
- Startup probe handles slow starts

**Verification Commands**:
```bash
# Note initial restart count
oc get pods

# Monitor pod during normal operation
oc logs -f <backend-pod>

# If liveness fails, pod should restart
oc get pods -w

# Check restart count
oc describe pod <backend-pod> | grep "Restart Count"
```

**Success Criteria**:
- ✅ Liveness failure triggers restart
- ✅ Readiness failure stops traffic
- ✅ Startup handles slow starts
- ✅ Probes detect failures

---

## Deliverable 11: Persistent Storage Testing

### Test Scenario 11.1: PVC Configuration Verification

**Objective**: Verify PVC is properly configured and bound

**Prerequisites**:
- PVC configured
- Storage class available

**Test Steps**:
1. Check PVC status: `oc get pvc`
2. Describe PVC: `oc describe pvc assetflow-uploads-pvc`
3. Verify storage class

**Expected Outcomes**:
- PVC is bound
- Storage capacity allocated
- Access mode correct

**Verification Commands**:
```bash
# Check PVC
oc get pvc
oc describe pvc assetflow-uploads-pvc

# Check storage class
oc get storageclass
oc describe pvc assetflow-uploads-pvc | grep -A 5 "StorageClass"

# Verify capacity
oc describe pvc assetflow-uploads-pvc | grep -A 5 "Capacity"
```

**Success Criteria**:
- ✅ PVC bound
- ✅ Capacity allocated
- ✅ Access mode correct
- ✅ No PVC errors

---

### Test Scenario 11.2: File Upload Testing

**Objective**: Verify file upload functionality works with persistent storage

**Prerequisites**:
- Storage demo deployment running
- PVC mounted

**Test Steps**:
1. Check storage demo pod: `oc get pods -l app=assetflow-backend-storage-demo`
2. Upload test file: `curl -X POST -F "file=@test.txt" https://assetflow-backend-.../uploads`
3. Verify file in pod: `oc exec -it <storage-pod> -- ls -la /app/uploads`

**Expected Outcomes**:
- File upload succeeds
- File appears in pod
- File persists across restarts

**Verification Commands**:
```bash
# Check storage demo pod
oc get pods -l app=assetflow-backend-storage-demo
oc describe pod <storage-demo-pod> | grep -A 10 "Mounts"

# Upload test file
echo "test content" > test.txt
curl -X POST -F "file=@test.txt" https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/uploads

# Verify file in pod
oc exec -it <storage-demo-pod> -- ls -la /app/uploads
oc exec -it <storage-demo-pod> -- cat /app/uploads/test.txt
```

**Success Criteria**:
- ✅ File upload succeeds
- ✅ File appears in pod
- ✅ File content correct
- ✅ No upload errors

---

### Test Scenario 11.3: Persistence Testing

**Objective**: Verify files persist across pod restarts

**Prerequisites**:
- File uploaded to PVC
- Storage demo pod running

**Test Steps**:
1. Upload test file
2. Note file content
3. Delete pod: `oc delete pod <storage-demo-pod>`
4. Wait for pod recreation
5. Verify file still exists

**Expected Outcomes**:
- File persists after pod deletion
- New pod can access file
- File content unchanged

**Verification Commands**:
```bash
# Upload test file
echo "persistence test" > persistence.txt
curl -X POST -F "file=@persistence.txt" https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/uploads

# Verify file exists
oc exec -it <storage-demo-pod> -- cat /app/uploads/persistence.txt

# Delete pod
oc delete pod <storage-demo-pod>

# Wait for recreation
sleep 30
oc get pods -l app=assetflow-backend-storage-demo

# Verify file persists
oc exec -it <new-storage-demo-pod> -- cat /app/uploads/persistence.txt
```

**Success Criteria**:
- ✅ File persists after restart
- ✅ New pod accesses file
- ✅ Content unchanged
- ✅ No data loss

---

## Deliverable 12: Monitoring and Logging Testing

### Test Scenario 12.1: Metrics Collection Verification

**Objective**: Verify metrics are being collected and accessible

**Prerequisites**:
- OpenShift monitoring available
- Application running

**Test Steps**:
1. Navigate to OpenShift Console → Observe → Monitoring
2. Query metrics: `container_cpu_usage_seconds_total`
3. Filter by assetflow pods
4. Verify data appears

**Expected Outcomes**:
- Metrics being collected
- Data accessible in console
- Metrics update in real-time

**Verification Commands**:
```bash
# Check metrics via CLI
oc top pods
oc top nodes

# Check metrics server
oc get pods -n openshift-monitoring | grep metrics

# Query Prometheus API
oc exec -n openshift-monitoring prometheus-k8s-0 -- curl -s 'http://localhost:9090/api/v1/query?query=container_cpu_usage_seconds_total{pod=~"assetflow-.*"}'
```

**Success Criteria**:
- ✅ Metrics collected
- ✅ Data accessible
- ✅ Real-time updates
- ✅ No metric errors

---

### Test Scenario 12.2: Log Collection Verification

**Objective**: Verify logs are being collected and accessible

**Prerequisites**:
- Application running
- Logging stack available

**Test Steps**:
1. Navigate to OpenShift Console → Observe → Logs
2. Filter by assetflow pods
3. View application logs
4. Verify log content

**Expected Outcomes**:
- Logs being collected
- Logs accessible in console
- Log content readable

**Verification Commands**:
```bash
# View logs via CLI
oc logs -l app=assetflow-backend
oc logs -l app=assetflow-frontend

# Follow logs in real-time
oc logs -f <pod-name>

# Check for structured logs
oc logs <backend-pod> | jq '.'
```

**Success Criteria**:
- ✅ Logs collected
- ✅ Logs accessible
- ✅ Content readable
- ✅ No log errors

---

### Test Scenario 12.3: Dashboard Verification

**Objective**: Verify monitoring dashboards are accessible and functional

**Prerequisites**:
- OpenShift monitoring available
- Application running

**Test Steps**:
1. Navigate to OpenShift Console → Observe → Monitoring → Dashboards
2. Open default dashboards
3. Verify assetflow metrics appear
4. Test custom queries

**Expected Outcomes**:
- Dashboards accessible
- Assetflow metrics visible
- Queries work correctly

**Verification Commands**:
```bash
# Access Grafana (if available)
oc port-forward svc/grafana 3000:3000 -n openshift-monitoring

# Check dashboard availability
oc get configmap -n openshift-monitoring | grep dashboard
```

**Success Criteria**:
- ✅ Dashboards accessible
- ✅ Metrics visible
- ✅ Queries work
- ✅ No dashboard errors

---

## Comprehensive Test Suite

### Full Test Execution

**Objective**: Execute all test scenarios to verify complete system functionality

**Prerequisites**:
- All deliverables deployed
- Test environment ready
- Documentation available

**Test Execution Order**:
1. Git Repository Testing (Deliverable 1)
2. CI/CD Pipeline Testing (Deliverable 2)
3. Kubernetes/OpenShift Manifests Testing (Deliverable 3)
4. Container Registry Testing (Deliverable 4)
5. Serverless Function Testing (Deliverable 5)
6. Load Balancing Testing (Deliverable 6)
7. Horizontal Pod Autoscaling Testing (Deliverable 7)
8. High Availability Testing (Deliverable 8)
9. Security Testing (Deliverable 9)
10. Health Probes Testing (Deliverable 10)
11. Persistent Storage Testing (Deliverable 11)
12. Monitoring and Logging Testing (Deliverable 12)

**Success Criteria**:
- ✅ All test scenarios pass
- ✅ No critical failures
- ✅ Documentation complete
- ✅ System ready for demo

---

## Test Automation

### Automated Test Script

```bash
#!/bin/bash

# AssetFlow Test Suite
# Run all test scenarios automatically

echo "Starting AssetFlow Test Suite..."

# Test 1: Git Repository
echo "Test 1: Git Repository Verification"
git ls-files | head -20
git grep -i "password\|secret" -- '*.yaml' '*.py' '*.js' || echo "No sensitive data found"

# Test 2: CI/CD Pipeline
echo "Test 2: CI/CD Pipeline Verification"
cat .github/workflows/ci-cd.yaml

# Test 3: Kubernetes Manifests
echo "Test 3: Kubernetes Manifests Verification"
oc get all
oc get configmaps
oc get secrets

# Test 4: Container Registry
echo "Test 4: Container Registry Verification"
docker pull ghcr.io/ayshrosine/assetflow-backend:latest
docker pull ghcr.io/ayshrosine/assetflow-frontend:latest

# Test 5: Serverless Function
echo "Test 5: Serverless Function Verification"
oc get ksvc
oc get pingsources

# Test 6: Load Balancing
echo "Test 6: Load Balancing Verification"
oc get endpoints assetflow-backend
oc get endpoints assetflow-frontend

# Test 7: HPA
echo "Test 7: HPA Verification"
oc get hpa
oc describe hpa assetflow-backend-hpa

# Test 8: High Availability
echo "Test 8: High Availability Verification"
oc get deployment assetflow-backend
oc get deployment assetflow-frontend
oc get pdb

# Test 9: Security
echo "Test 9: Security Verification"
oc describe route assetflow-frontend | grep -A 5 "TLS"
oc get secrets
oc get serviceaccounts
oc get networkpolicy

# Test 10: Health Probes
echo "Test 10: Health Probes Verification"
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/readyz

# Test 11: Persistent Storage
echo "Test 11: Persistent Storage Verification"
oc get pvc
oc get pods -l app=assetflow-backend-storage-demo

# Test 12: Monitoring and Logging
echo "Test 12: Monitoring and Logging Verification"
oc top pods
oc logs -l app=assetflow-backend --tail=20

echo "Test Suite Complete!"
```

---

## Test Reporting

### Test Results Template

```markdown
# AssetFlow Test Results

**Date**: [Test Date]
**Tester**: [Tester Name]
**Environment**: [OpenShift Cluster]

## Test Summary
- Total Tests: [Number]
- Passed: [Number]
- Failed: [Number]
- Skipped: [Number]

## Test Results by Deliverable

### Deliverable 1: Git Repository
- [ ] Test 1.1: Repository Structure Verification - [PASS/FAIL]
- [ ] Test 1.2: Security Best Practices Verification - [PASS/FAIL]

### Deliverable 2: CI/CD Pipeline
- [ ] Test 2.1: CI/CD Workflow Verification - [PASS/FAIL]
- [ ] Test 2.2: Automated Build Testing - [PASS/FAIL]
- [ ] Test 2.3: Automated Deployment Testing - [PASS/FAIL]

[Continue for all deliverables...]

## Issues Found
1. [Issue Description]
2. [Issue Description]

## Recommendations
1. [Recommendation]
2. [Recommendation]

## Sign-off
**Tester**: [Name]
**Date**: [Date]
```

---

## Conclusion

This comprehensive test suite provides detailed procedures for validating all 12 hackathon deliverables. Each test scenario includes specific steps, expected outcomes, and verification commands to ensure thorough validation of the AssetFlow application on OpenShift.

Regular execution of these test scenarios will ensure the system remains functional and meets all requirements throughout the development and deployment lifecycle.

For additional information, refer to:
- VERIFICATION_CHECKLIST.md - Detailed verification procedures
- TROUBLESHOOTING_GUIDE.md - Common issues and solutions
- MONITORING_GUIDE.md - Monitoring setup and usage
- DEMO_SCRIPT.md - Live demonstration procedures