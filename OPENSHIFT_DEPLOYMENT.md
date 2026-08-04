# AssetFlow OpenShift Deployment Guide

This guide covers deploying AssetFlow to Red Hat OpenShift with all 12 hackathon deliverables.

## Prerequisites

- **OpenShift Access**: Company-provided OpenShift environment
- **Docker**: Installed and running locally
- **OpenShift CLI (oc)**: Installed and configured
- **GitHub Account**: For GitHub Container Registry
- **MongoDB Atlas**: External MongoDB database
- **Google Cloud Console**: For Google OAuth credentials

## Environment Variables

Set these environment variables before deployment:

```bash
# MongoDB
export MONGO_URL="mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>"

# Application
export JWT_SECRET="<generate strong secret>"
export ENV="production"

# Google OAuth
export GOOGLE_CLIENT_ID="<from Google Console>"
export GOOGLE_CLIENT_SECRET="<from Google Console>"

# Demo Credentials
export ADMIN_PASSWORD="<demo-only>"

# OpenShift
export NAMESPACE="assetflow"
export OPENSHIFT_SERVER="<your-openshift-server>"
export OPENSHIFT_TOKEN="<your-openshift-token>"
```

## Local Container Testing

Before deploying to OpenShift, test containers locally:

```bash
# Build and test backend
cd backend
docker build -t assetflow-backend:test .
docker run -p 8000:8000 \
  -e MONGO_URL="$MONGO_URL" \
  -e DB_NAME="assetflow" \
  -e JWT_SECRET="$JWT_SECRET" \
  -e ENV="development" \
  assetflow-backend:test

# Test health endpoints
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/startupz

# Build and test frontend
cd ../frontend
docker build -t assetflow-frontend:test .
docker run -p 8080:8080 assetflow-frontend:test
curl http://localhost:8080/
```

## Building and Pushing Images

### Using GitHub Container Registry

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u <your-username> --password-stdin

# Build and push backend
cd backend
docker build -t ghcr.io/<your-username>/assetflow-backend:latest .
docker push ghcr.io/<your-username>/assetflow-backend:latest

# Build and push frontend
cd ../frontend
docker build -t ghcr.io/<your-username>/assetflow-frontend:latest .
docker push ghcr.io/<your-username>/assetflow-frontend:latest
```

## OpenShift Deployment

### Manual Deployment

```bash
# Login to OpenShift
oc login --server=$OPENSHIFT_SERVER --token=$OPENSHIFT_TOKEN

# Create namespace
oc new-project assetflow

# Create secrets
oc create secret generic assetflow-secrets \
  --from-literal=MONGO_URL="$MONGO_URL" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  --from-literal=GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD"

# Apply manifests
oc apply -k k8s/base

# Update images
oc set image deployment/assetflow-backend backend=ghcr.io/<your-username>/assetflow-backend:latest
oc set image deployment/assetflow-frontend frontend=ghcr.io/<your-username>/assetflow-frontend:latest

# Wait for rollout
oc rollout status deployment/assetflow-backend
oc rollout status deployment/assetflow-frontend
```

### Using Deployment Script

```bash
# Set environment variables
export NAMESPACE="assetflow"
export BACKEND_IMAGE="ghcr.io/<your-username>/assetflow-backend:latest"
export FRONTEND_IMAGE="ghcr.io/<your-username>/assetflow-frontend:latest"

# Run deployment script
chmod +x scripts/deploy-openshift.sh
./scripts/deploy-openshift.sh
```

## Verifying Deployment

### Check Pod Status

```bash
oc get pods
oc describe pod <pod-name>
```

### Check Routes

```bash
oc get routes
```

### Check Services

```bash
oc get services
```

### Check HPA

```bash
oc get hpa
oc describe hpa assetflow-backend-hpa
```

### Check PVC

```bash
oc get pvc
oc describe pvc assetflow-uploads-pvc
```

### Check Serverless Resources

```bash
oc get ksvc
oc get pingsources
```

## Testing Deliverables

### 1. Health Probes

```bash
# Get backend route
BACKEND_ROUTE=$(oc get route assetflow-backend -o jsonpath='{.spec.host}')

# Test health endpoints
curl https://$BACKEND_ROUTE/healthz
curl https://$BACKEND_ROUTE/readyz
curl https://$BACKEND_ROUTE/startupz
```

### 2. Load Balancing

```bash
# Test with curl loop
for i in {1..20}; do
  curl -s https://$BACKEND_ROUTE/healthz
  echo
done
```

### 3. Horizontal Pod Autoscaling

```bash
# Install load testing tool
# (Use hey, k6, or similar)

# Generate load
hey -z 2m -c 50 https://$BACKEND_ROUTE/healthz

# Watch HPA in another terminal
oc get hpa -w
oc get pods -w
```

### 4. Zero-Downtime Rolling Updates

```bash
# Continuous curl loop
while true; do
  curl -s -o /dev/null -w "%{http_code}\n" https://$BACKEND_ROUTE/healthz
  sleep 0.5
done

# Trigger rolling update in another terminal
oc rollout restart deployment/assetflow-backend
```

### 5. Security

```bash
# Check TLS
curl -I https://$BACKEND_ROUTE/healthz

# Check secrets
oc get secret assetflow-secrets

# Check RBAC
oc auth can-i list pods --as=system:serviceaccount:assetflow:assetflow-backend-sa
oc auth can-i delete deployments --as=system:serviceaccount:assetflow:assetflow-backend-sa

# Check NetworkPolicy
oc get networkpolicy
```

### 6. Persistent Storage

```bash
# Upload a file via the application
# Delete a backend pod
oc delete pod <backend-pod-name>

# Verify file is still accessible after pod recreation
```

### 7. Serverless Function

```bash
# Check Knative Service
oc get ksvc assetflow-reminder-job

# Check if it scales to zero
oc get pods

# Trigger manually
oc create -f k8s/base/knative-ping-source.yaml

# Watch pod appear and disappear
oc get pods -w
```

### 8. Monitoring

```bash
# Check OpenShift Observe dashboard
# Navigate to: Developer → Observe → Dashboards

# Check logs
oc logs -f deployment/assetflow-backend
oc logs -f deployment/assetflow-frontend

# Check metrics
oc get metrics
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod logs
oc logs <pod-name>

# Check pod events
oc describe pod <pod-name>

# Check if secrets exist
oc get secret assetflow-secrets
```

### HPA Not Scaling

```bash
# Check metrics server
oc get apiservice | grep metrics

# Check HPA events
oc describe hpa assetflow-backend-hpa

# Check resource requests/limits
oc describe deployment assetflow-backend
```

### NetworkPolicy Issues

```bash
# Check network policies
oc get networkpolicy

# Describe network policy
oc describe networkpolicy <policy-name>

# Test connectivity
oc run tmp --image=busybox --rm -it --restart=Never -- sh
```

### PVC Issues

```bash
# Check PVC status
oc get pvc
oc describe pvc assetflow-uploads-pvc

# Check storage class
oc get storageclass
```

## CI/CD Pipeline

### GitHub Actions Setup

1. Add secrets to GitHub repository:
   - `GITHUB_TOKEN` (automatically available)
   - `OPENSHIFT_SERVER`
   - `OPENSHIFT_TOKEN`
   - `OPENSHIFT_NAMESPACE`

2. Uncomment the deploy job in `.github/workflows/ci-cd.yaml`

3. Push to main branch to trigger pipeline

### Manual CI/CD Steps

```bash
# Run tests
cd backend
pytest

# Build images
docker build -t ghcr.io/<username>/assetflow-backend:latest ./backend
docker build -t ghcr.io/<username>/assetflow-frontend:latest ./frontend

# Push images
docker push ghcr.io/<username>/assetflow-backend:latest
docker push ghcr.io/<username>/assetflow-frontend:latest

# Deploy to OpenShift
oc set image deployment/assetflow-backend backend=ghcr.io/<username>/assetflow-backend:latest
oc set image deployment/assetflow-frontend frontend=ghcr.io/<username>/assetflow-frontend:latest
oc rollout status deployment/assetflow-backend
oc rollout status deployment/assetflow-frontend
```

## Cleanup

```bash
# Delete all resources
oc delete -k k8s/base

# Delete namespace
oc delete project assetflow

# Or delete specific resources
oc delete deployment assetflow-backend
oc delete deployment assetflow-frontend
oc delete service assetflow-backend
oc delete service assetflow-frontend
oc delete route assetflow-backend
oc delete route assetflow-frontend
oc delete hpa assetflow-backend-hpa
oc delete pdb assetflow-backend-pdb
oc delete secret assetflow-secrets
oc delete configmap assetflow-config
oc delete pvc assetflow-uploads-pvc
oc delete networkpolicy --all
oc delete serviceaccount assetflow-backend-sa
oc delete role assetflow-pod-reader
oc delete rolebinding assetflow-backend-binding
oc delete ksvc assetflow-reminder-job
oc delete pingsource reminder-cron
```

## Notes

- **MongoDB**: Uses external MongoDB Atlas, not in-cluster
- **Storage**: PVC for uploads only (ReadWriteOnce limitation)
- **Serverless**: Knative Service scales to zero when idle
- **NetworkPolicy**: Default-deny with explicit allows
- **RBAC**: Namespace-scoped permissions only
- **Resource Limits**: Adjust based on your OpenShift quota
- **Image Registry**: Using GitHub Container Registry (GHCR)

## Additional Resources

- [OpenShift Documentation](https://docs.openshift.com/)
- [Knative Documentation](https://knative.dev/docs/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [MongoDB Atlas](https://docs.atlas.mongodb.com/)
