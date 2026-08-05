# AssetFlow - OpenShift Hackathon Project

## Overview

AssetFlow is a comprehensive asset management system deployed on Red Hat OpenShift, demonstrating modern cloud-native practices including microservices architecture, serverless computing, and GitOps-based continuous deployment. This project successfully implements all 12 hackathon deliverables for enterprise-grade application deployment.

## 🚀 Quick Start

### Prerequisites
- OpenShift cluster access (Developer Sandbox or full cluster)
- oc CLI tool installed and configured
- Docker installed (for local testing)
- GitHub account (for CI/CD)

### Deployment

1. **Clone the repository**
```bash
git clone https://github.com/ayshrosine/red_hat_assets.git
cd red_hat_assets
```

2. **Configure OpenShift secrets**
```bash
# Create secret from template
oc create secret generic assetflow-secrets \
  --from-literal=MONGO_URL=<your-mongo-url> \
  --from-literal=JWT_SECRET=<your-jwt-secret> \
  --from-literal=GOOGLE_CLIENT_ID=<your-google-client-id> \
  --from-literal=GOOGLE_CLIENT_SECRET=<your-google-client-secret> \
  --from-literal=ADMIN_PASSWORD=<admin-password> \
  --from-literal=ADMIN_EMAIL=admin@assetflow.io \
  --from-literal=EMERGENT_LLM_KEY=<optional-llm-key>
```

3. **Deploy to OpenShift**
```bash
# Apply all Kubernetes manifests
oc apply -f k8s/base/

# Verify deployment
oc get pods
oc get all
```

4. **Access the application**
```bash
# Get route URLs
oc get routes

# Frontend: https://assetflow-frontend-<namespace>.apps.<cluster>.com
# Backend: https://assetflow-backend-<namespace>.apps.<cluster>.com
```

## 📋 Hackathon Deliverables

All 12 hackathon deliverables have been successfully implemented and verified:

### ✅ 1. Source Code in Git Repository
- Repository: https://github.com/ayshrosine/red_hat_assets
- Complete source code for backend (FastAPI + Python)
- Complete source code for frontend (React + JavaScript)
- Proper directory structure and documentation
- Security best practices with .gitignore and secret templates

### ✅ 2. CI/CD Pipeline Configuration
- GitHub Actions workflow: `.github/workflows/ci-cd.yaml`
- Automated build, test, and deployment
- Container image pushing to GitHub Container Registry (GHCR)
- Automated OpenShift deployment via oc CLI
- Build-time environment variable handling

### ✅ 3. Kubernetes/OpenShift Deployment Manifests
- 18 comprehensive YAML manifests in `k8s/base/`
- Deployments, Services, Routes, ConfigMaps, Secrets
- Horizontal Pod Autoscaler (HPA) configuration
- Pod Disruption Budget (PDB) for high availability
- RBAC (ServiceAccount, Role, RoleBinding)
- Network Policies for security
- Knative serverless components

### ✅ 4. Container Image in Container Registry
- Backend image: `ghcr.io/ayshrosine/assetflow-backend:latest`
- Frontend image: `ghcr.io/ayshrosine/assetflow-frontend:latest`
- Multi-stage builds for optimization
- OpenShift-compatible (non-root, proper permissions)
- Versioned images with commit SHA tags

### ✅ 5. Serverless Function Implementation
- Knative service: `assetflow-reminder-service`
- Event-driven reminder function for overdue assets
- PingSource for cron-based triggering (every 5 minutes)
- Scales to zero when not in use
- Cloud-native architecture

### ✅ 6. Load Balancing Across Multiple Instances
- OpenShift Services (ClusterIP) for internal load balancing
- OpenShift Routes for external load balancing with TLS
- Round-robin distribution across pods
- Multiple backend replicas (2 pods)
- Multiple frontend replicas (2 pods)

### ✅ 7. Horizontal Pod Autoscaling (HPA)
- HPA configured for backend deployment
- CPU-based autoscaling (60% utilization target)
- Min replicas: 2, Max replicas: 6
- Metrics server integration
- Automatic scale-up and scale-down

### ✅ 8. High Availability with Multiple Replicas
- Rolling update strategy (zero downtime)
- Pod Disruption Budget (minimum 1 available pod)
- Health probes (liveness, readiness, startup)
- Multiple replicas across nodes
- Graceful pod termination

### ✅ 9. Security Implementation
- TLS/SSL with edge termination on Routes
- Kubernetes Secrets for sensitive data
- RBAC with least-privilege access
- Network Policies (default-deny with explicit allow)
- No hardcoded credentials in source code
- Proper CORS configuration

### ✅ 10. Health Probes
- `/healthz` - Liveness endpoint
- `/readyz` - Readiness endpoint  
- `/startupz` - Startup endpoint
- Configured in deployments with appropriate thresholds
- Automatic restart on failure

### ✅ 11. Persistent Storage
- PVC for file uploads (`assetflow-uploads-pvc`)
- Dedicated storage demo deployment (single replica)
- Main deployment uses ephemeral storage for HA
- 1Gi storage capacity
- ReadWriteOnce access mode

### ✅ 12. Monitoring and Logging Dashboard
- OpenShift built-in monitoring (Observe tab)
- CPU, memory, and network metrics
- Centralized log aggregation
- Structured JSON logging
- Real-time dashboards and alerts
- Log viewing via console and CLI

## 📁 Project Structure

```
red_hat_assets/
├── backend/                 # FastAPI backend application
│   ├── routers/            # API route handlers
│   ├── deps.py             # Dependencies and database
│   ├── server.py           # Main application server
│   ├── Dockerfile          # Backend container image
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── src/               # React components and pages
│   ├── public/            # Static assets
│   ├── Dockerfile         # Frontend container image
│   └── package.json       # Node dependencies
├── k8s/base/             # Kubernetes/OpenShift manifests
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── backend-service.yaml
│   ├── frontend-service.yaml
│   ├── backend-route.yaml
│   ├── frontend-route.yaml
│   ├── backend-hpa.yaml
│   ├── backend-pdb.yaml
│   ├── configmap.yaml
│   ├── secret-template.yaml
│   ├── pvc-uploads.yaml
│   ├── rbac.yaml
│   ├── networkpolicy.yaml
│   ├── knative-reminder-service.yaml
│   ├── knative-ping-source.yaml
│   └── kustomization.yaml
├── .github/workflows/    # CI/CD configuration
│   └── ci-cd.yaml
├── docs/                 # Additional documentation
├── scripts/              # Deployment and utility scripts
├── VERIFICATION_CHECKLIST.md    # Comprehensive verification procedures
├── DEMO_SCRIPT.md              # Live demonstration script
├── TROUBLESHOOTING_GUIDE.md    # Common issues and solutions
├── MONITORING_GUIDE.md         # Monitoring setup and usage
├── TEST_SCENARIOS.md           # Detailed test procedures
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

Key environment variables are configured via ConfigMap and Secret:

**ConfigMap (`assetflow-config`)**:
- `ENV`: Environment (production/development)
- `CORS_ORIGINS`: CORS allowed origins
- `BACKEND_URL`: Backend service URL
- `FRONTEND_URL`: Frontend route URL
- `GOOGLE_CLIENT_ID`: Google OAuth Client ID
- `ADMIN_EMAIL`: Admin email address

**Secret (`assetflow-secrets`)**:
- `MONGO_URL`: MongoDB Atlas connection string
- `JWT_SECRET`: JWT signing secret
- `GOOGLE_CLIENT_SECRET`: Google OAuth Client Secret
- `ADMIN_PASSWORD`: Admin password
- `EMERGENT_LLM_KEY`: Optional LLM API key

### Build-Time Variables

Frontend requires build-time environment variables (React limitation):
- `REACT_APP_GOOGLE_CLIENT_ID`: Google OAuth Client ID
- `REACT_APP_BACKEND_URL`: Production backend route URL

These are passed as Docker build arguments in CI/CD pipeline.

## 📊 Monitoring and Logging

### OpenShift Console Monitoring

1. Navigate to OpenShift Console → Observe → Monitoring
2. View metrics dashboards for CPU, memory, and network
3. Access logs via Observe → Logs
4. Set up alerts for critical metrics

### CLI Monitoring

```bash
# Resource usage
oc top pods
oc top nodes

# Application logs
oc logs -l app=assetflow-backend
oc logs -l app=assetflow-frontend

# Health endpoints
curl https://assetflow-backend-<namespace>.apps.<cluster>.com/healthz
curl https://assetflow-backend-<namespace>.apps.<cluster>.com/readyz
```

For detailed monitoring guidance, see [MONITORING_GUIDE.md](MONITORING_GUIDE.md).

## 🧪 Testing

### Verification Checklist

Run the comprehensive verification checklist:
```bash
# Review the checklist
cat VERIFICATION_CHECKLIST.md
```

### Test Scenarios

Execute detailed test scenarios for each deliverable:
```bash
# Review test procedures
cat TEST_SCENARIOS.md
```

### Quick Health Check

```bash
# Check all pods
oc get pods

# Check all resources
oc get all

# Test health endpoints
curl https://assetflow-backend-<namespace>.apps.<cluster>.com/healthz
curl https://assetflow-frontend-<namespace>.apps.<cluster>.com/
```

## 🎭 Demo Preparation

### Live Demonstration

For hackathon demonstrations, follow the comprehensive demo script:
```bash
# Review demo procedures
cat DEMO_SCRIPT.md
```

The demo script includes:
- 12-section walkthrough (27-30 minutes total)
- Backup procedures for each section
- Pre-demo preparation checklist
- Troubleshooting guidance

### Demo Environment Setup

1. Ensure all pods are running: `oc get pods`
2. Verify routes are accessible: `oc get routes`
3. Open OpenShift Console in browser
4. Prepare terminal with oc CLI
5. Have backup commands ready

## 🛠️ Troubleshooting

### Common Issues

For common issues and solutions, refer to:
```bash
cat TROUBLESHOOTING_GUIDE.md
```

### Quick Fixes

**Pods not starting**:
```bash
oc describe pod <pod-name>
oc logs <pod-name>
oc delete pod <stuck-pod>
```

**Routes not accessible**:
```bash
oc get routes
oc describe route <route-name>
oc get endpoints <service-name>
```

**HPA not scaling**:
```bash
oc get hpa
oc describe hpa assetflow-backend-hpa
oc top pods
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline automatically:
1. Builds backend and frontend Docker images
2. Pushes images to GitHub Container Registry
3. Deploys to OpenShift using oc CLI
4. Updates deployments with new images
5. Verifies rollout status

### Manual Workflow Trigger

```bash
# Requires GitHub CLI
gh workflow run ci-cd
gh run list --workflow=ci-cd.yaml
```

## 🔐 Security Considerations

### Implemented Security Features

- **TLS/SSL**: Edge termination on all Routes
- **Secrets Management**: Kubernetes Secrets for sensitive data
- **RBAC**: ServiceAccount with minimal permissions
- **Network Policies**: Default-deny with explicit allow rules
- **No Hardcoded Credentials**: All secrets externalized
- **CORS Configuration**: Proper cross-origin resource sharing
- **Health Probes**: Security monitoring via probe failures

### Security Best Practices

- Regular secret rotation
- Minimal RBAC permissions
- Network segmentation via policies
- Regular security updates
- Log monitoring for suspicious activity

## 📈 Performance

### Resource Configuration

**Backend**:
- CPU Request: 100m, Limit: 500m
- Memory Request: 256Mi, Limit: 512Mi
- Replicas: 2 (autoscaling 2-6)

**Frontend**:
- CPU Request: 50m, Limit: 200m
- Memory Request: 128Mi, Limit: 256Mi
- Replicas: 2

### Autoscaling

HPA scales based on CPU utilization:
- Target: 60% CPU utilization
- Min replicas: 2
- Max replicas: 6
- Scale-up: Immediate
- Scale-down: 5-minute stabilization window

## 🌐 Architecture

### System Architecture

```
┌─────────────────┐
│   Browser       │
│   (React UI)    │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│  OpenShift      │
│  Router (TLS)   │
└────────┬────────┘
         │ HTTP
         ↓
┌─────────────────┐
│  Frontend Pods  │
│  (2 replicas)   │
└────────┬────────┘
         │ API Calls
         ↓
┌─────────────────┐
│  Backend Pods   │
│  (2 replicas)   │
└────────┬────────┘
         │ Database
         ↓
┌─────────────────┐
│  MongoDB Atlas  │
│  (External)     │
└─────────────────┘
```

### Serverless Component

```
┌─────────────────┐
│  PingSource     │
│  (Cron: 5min)   │
└────────┬────────┘
         │ Events
         ↓
┌─────────────────┐
│  Knative Service│
│  (Reminder)     │
└────────┬────────┘
         │ API Calls
         ↓
┌─────────────────┐
│  MongoDB Atlas  │
└─────────────────┘
```

## 📚 Documentation

### Core Documentation

- **[VERIFICATION_CHECKLIST.md](VERIFICATION_CHECKLIST.md)** - Comprehensive verification of all 12 deliverables
- **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** - Live demonstration script with 12 sections
- **[TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)** - Common issues and solutions
- **[MONITORING_GUIDE.md](MONITORING_GUIDE.md)** - Monitoring setup and usage
- **[TEST_SCENARIOS.md](TEST_SCENARIOS.md)** - Detailed test procedures

### Additional Documentation

- **[AssetFlow-OpenShift-Hackathon-Guide.md](AssetFlow-OpenShift-Hackathon-Guide.md)** - Implementation guide
- **[OPENSHIFT_DEPLOYMENT.md](OPENSHIFT_DEPLOYMENT.md)** - Deployment procedures
- **[frontend/README.md](frontend/README.md)** - Frontend-specific documentation

## 🤝 Contributing

This project was developed for the Red Hat OpenShift Hackathon. For questions or issues:

1. Review the troubleshooting guide
2. Check test scenarios for verification
3. Consult the monitoring guide for operational issues
4. Refer to demo script for demonstration procedures

## 📝 License

This project is licensed under the Apache License 2.0.

## 🎯 Success Criteria

All 12 hackathon deliverables have been successfully implemented:

- ✅ Source code hosted in Git repository
- ✅ CI/CD pipeline configured and functional
- ✅ Kubernetes/OpenShift manifests deployed
- ✅ Container images in registry
- ✅ Serverless function implemented
- ✅ Load balancing across instances
- ✅ Horizontal Pod Autoscaling configured
- ✅ High availability with rolling updates
- ✅ Security implementation complete
- ✅ Health probes operational
- ✅ Persistent storage configured
- ✅ Monitoring and logging dashboard functional

## 🚀 Next Steps

1. **Review Documentation**: Start with VERIFICATION_CHECKLIST.md
2. **Deploy Application**: Follow deployment procedures
3. **Verify Functionality**: Run test scenarios
4. **Prepare Demo**: Use DEMO_SCRIPT.md for presentation
5. **Monitor System**: Follow MONITORING_GUIDE.md for operations

---

**Project Status**: ✅ Complete - All deliverables implemented and verified

**Last Updated**: 2026-08-05

**OpenShift Version**: Compatible with OpenShift 4.x

**Kubernetes Version**: Compatible with Kubernetes 1.25+