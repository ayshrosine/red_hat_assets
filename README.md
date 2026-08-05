# AssetFlow - OpenShift Hackathon Project

## 🚀 Live Deployment

**Frontend Application:** https://assetflow-frontend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com  
**Backend API:** https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com

## Overview

AssetFlow is a comprehensive asset management system deployed on Red Hat OpenShift, demonstrating modern cloud-native practices including microservices architecture, serverless computing, and GitOps-based continuous deployment. This project successfully implements all 12 hackathon deliverables for enterprise-grade application deployment.

## 🌟 Key Features

- **Modern Tech Stack**: React frontend with FastAPI backend
- **Cloud-Native Architecture**: Kubernetes/OpenShift deployment with microservices
- **Serverless Components**: Knative-based event-driven functions
- **Auto-scaling**: Horizontal Pod Autoscaler for dynamic resource management
- **High Availability**: Multi-replica deployments with rolling updates
- **Security**: TLS/SSL, RBAC, Network Policies, and Secrets management
- **CI/CD**: GitHub Actions pipeline with automated deployment
- **Monitoring**: Built-in OpenShift monitoring and logging

## 🛠️ Technology Stack

### Frontend
- **Framework**: React 18 with JavaScript
- **UI Library**: Custom components with modern design
- **State Management**: React Context API
- **HTTP Client**: Axios with interceptors
- **Authentication**: Google OAuth + JWT
- **Build Tool**: Create React App with Craco

### Backend
- **Framework**: FastAPI (Python 3.11)
- **Database**: MongoDB Atlas
- **Authentication**: JWT + Google OAuth
- **API Documentation**: OpenAPI/Swagger
- **File Upload**: Multer for asset attachments
- **Background Tasks**: Celery-style job processing

### Infrastructure
- **Platform**: Red Hat OpenShift (Kubernetes)
- **Container Registry**: GitHub Container Registry (GHCR)
- **Ingress**: OpenShift Routes with TLS
- **Serverless**: Knative Serving and Eventing
- **CI/CD**: GitHub Actions
- **Monitoring**: OpenShift Monitoring Stack

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend│────▶│  OpenShift Route│────▶│  Nginx Reverse  │
│   (2 replicas)  │     │  (TLS/SSL)      │     │  Proxy          │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Google OAuth   │◀────│  OpenShift Route│◀────│  FastAPI Backend │
│  Service        │     │  (TLS/SSL)      │     │  (2 replicas)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                            ┌────────────────────────────┼────────────────────────────┐
                            │                            │                            │
                            ▼                            ▼                            ▼
                   ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
                   │ MongoDB Atlas│            │   Knative    │            │   Persistent │
                   │  (Cloud DB)  │            │  Reminder    │            │   Storage    │
                   └──────────────┘            │  Service     │            │   (PVC)      │
                                               └──────────────┘            └──────────────┘
```

### Component Details

**Frontend Layer:**
- React SPA with client-side routing
- Nginx for static file serving
- Google OAuth integration
- Real-time dashboard updates

**Backend Layer:**
- FastAPI REST API
- JWT authentication middleware
- File upload handling
- Background job processing

**Data Layer:**
- MongoDB Atlas for primary data
- Persistent Volume Claim for file storage
- Redis for session management (optional)

**Infrastructure Layer:**
- OpenShift Routes for external access
- Services for internal load balancing
- Horizontal Pod Autoscaler for scaling
- Network Policies for security

## 📋 Deployment Process & Changes Made

### Initial Deployment Challenges

1. **Frontend Environment Variables Issue**
   - **Problem**: React environment variables not being baked into the build
   - **Solution**: Modified Dockerfile to use ARG and ENV directives for build-time variables
   - **Impact**: Frontend can now communicate with backend API correctly

2. **Backend URL Configuration**
   - **Problem**: Internal Kubernetes service name used instead of external route
   - **Solution**: Updated CI/CD pipeline to use external OpenShift route URL
   - **Impact**: API calls now work from user's browser

3. **Nginx Redirect Loop**
   - **Problem**: Conflicting location blocks causing 302 redirect loop
   - **Solution**: Restructured nginx.conf with proper routing configuration
   - **Impact**: Frontend loads correctly without redirect issues

4. **CI/CD GHCR Authentication**
   - **Problem**: GitHub Container Registry authentication failure
   - **Solution**: Added explicit permissions and proper token usage in workflow
   - **Impact**: Automated pipeline now successfully pushes images

5. **Google OAuth Configuration**
   - **Problem**: Frontend URL not in authorized JavaScript origins
   - **Solution**: Added OpenShift route URL to Google Cloud Console
   - **Impact**: Google OAuth login now works correctly

### Final Deployment Configuration

**Frontend Deployment:**
- Image: `ghcr.io/ayshrosine/assetflow-frontend:fixed`
- Replicas: 2 (with HPA support)
- Environment variables baked at build time
- Nginx configured for SPA routing
- Health probes configured

**Backend Deployment:**
- Image: `ghcr.io/ayshrosine/assetflow-backend:latest`
- Replicas: 2 (with HPA: 2-6 pods)
- Connected to MongoDB Atlas
- JWT + Google OAuth authentication
- Health probes: `/healthz`, `/readyz`, `/startupz`

**Infrastructure:**
- TLS/SSL enabled on all routes
- Network policies for security
- RBAC configured with least privilege
- Persistent storage for file uploads
- Knative service for serverless functions

## 📊 Key Learnings

### Technical Learnings

1. **React Build-Time Variables**
   - React environment variables must be baked in at build time
   - Cannot be changed at runtime in the container
   - Requires Docker build arguments for proper configuration

2. **OpenShift Networking**
   - Internal service names vs external route URLs
   - Service-to-service communication uses cluster DNS
   - External access requires Routes with proper TLS configuration

3. **CI/CD Pipeline Configuration**
   - GitHub Actions permissions for container registry access
   - Token management for secure authentication
   - Build-time vs runtime environment variable handling

4. **Container Orchestration**
   - Rolling update strategies for zero-downtime deployments
   - Health probes are critical for container orchestration
   - Resource limits and requests for proper pod scheduling

5. **Serverless Architecture**
   - Knative provides powerful serverless capabilities on Kubernetes
   - Event-driven architecture with PingSource for cron jobs
   - Scale-to-zero functionality for cost optimization

### Process Learnings

1. **Incremental Deployment**
   - Start with basic deployment, then add features
   - Test each component individually before integration
   - Use manual deployment for debugging before CI/CD automation

2. **Monitoring and Debugging**
   - OpenShift console provides excellent visibility
   - Log aggregation is essential for troubleshooting
   - Health checks help identify issues early

3. **Security Considerations**
   - Never hardcode credentials in source code
   - Use Kubernetes Secrets for sensitive data
   - Implement proper RBAC and network policies

4. **Configuration Management**
   - Separate configuration from code
   - Use ConfigMaps for non-sensitive config
   - Use Secrets for sensitive data

## ✅ Pros and Cons of OpenShift Deployment

### Pros

**1. Developer Experience**
- Excellent web console with intuitive UI
- Built-in monitoring and logging dashboards
- Rich CLI tool (`oc`) with advanced features
- Streamlined deployment workflows

**2. Security**
- Built-in security features (RBAC, Network Policies)
- Integrated secret management
- Automatic TLS/SSL certificate management
- Regular security updates and patches

**3. Scalability**
- Horizontal Pod Autoscaler for automatic scaling
- Load balancing built-in
- Support for multiple availability zones
- Resource quotas and limits

**4. Enterprise Features**
- High availability with multiple replicas
- Rolling updates for zero-downtime deployments
- Pod Disruption Budgets for planned maintenance
- Advanced networking with ingress controllers

**5. Ecosystem Integration**
- Knative for serverless workloads
- Operator framework for application management
- Rich catalog of certified operators
- Integration with Red Hat ecosystem

**6. CI/CD Integration**
- Native GitOps support with ArgoCD
- GitHub Actions integration
- Automated build and deployment pipelines
- Image registry integration

### Cons

**1. Complexity**
- Steep learning curve for beginners
- Many concepts to understand (Pods, Services, Routes, etc.)
- Configuration can be verbose and complex
- Requires YAML manifest management

**2. Resource Requirements**
- Requires significant system resources
- Not suitable for very small projects
- Development environment can be resource-heavy
- Cluster setup and maintenance overhead

**3. Cost**
- Production clusters can be expensive
- Development sandbox has limitations
- Storage costs for persistent volumes
- Network egress charges may apply

**4. Debugging Challenges**
- Distributed system debugging is complex
- Log aggregation can be overwhelming
- Network issues harder to diagnose
- Container startup failures can be cryptic

**5. Vendor Lock-in**
- OpenShift-specific features and APIs
- Migration to other platforms requires adaptation
- Proprietary extensions and operators
- Learning investment is platform-specific

**6. Development Workflow**
- Local development differs from production
- Container build cycles can be slow
- Testing requires cluster or minishift
- Hot-reload not as seamless as traditional dev

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
│   ├── nginx.conf         # Nginx configuration
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
├── scripts/              # Deployment and utility scripts
│   ├── build-and-push.sh
│   ├── deploy-openshift.sh
│   └── local-test.sh
├── .gitignore            # Git ignore patterns
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

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

# Pod status
oc get pods -w
oc describe pod <pod-name>
```

## 🔒 Security Considerations

- All sensitive data stored in Kubernetes Secrets
- TLS/SSL enabled on all external routes
- RBAC configured with least-privilege access
- Network policies restrict pod-to-pod communication
- No hardcoded credentials in source code
- Regular security updates via OpenShift

## 🐛 Troubleshooting

### Common Issues

**Frontend shows blank screen:**
- Check if backend URL is correctly configured
- Verify environment variables are baked into the build
- Check nginx configuration for routing issues

**Google OAuth fails:**
- Ensure frontend URL is in Google Cloud Console authorized origins
- Verify Google Client ID and Secret are correct
- Check CORS configuration

**Pods not starting:**
- Check resource limits and requests
- Verify image pull secrets are configured
- Review pod logs for error messages

**API calls failing:**
- Verify backend service is accessible
- Check network policies allow traffic
- Review CORS configuration

## 📈 Performance

### Current Configuration
- **Frontend**: 2 replicas, 200m CPU limit, 256Mi memory limit
- **Backend**: 2 replicas (HPA: 2-6), 500m CPU limit, 512Mi memory limit
- **Autoscaling**: CPU-based (60% target)
- **Storage**: 1Gi persistent volume for uploads

### Optimization Tips
- Use horizontal pod autoscaling for variable workloads
- Implement caching for frequently accessed data
- Optimize database queries with proper indexing
- Use CDN for static assets in production

## 🤝 Contributing

This project was developed for the Red Hat OpenShift Hackathon. For questions or suggestions, please open an issue in the repository.

## 📄 License

This project is open source and available under the MIT License.

## 🎯 Hackathon Deliverables Status

✅ **All 12 deliverables completed and verified:**
1. Source code in Git repository
2. CI/CD pipeline configuration
3. Kubernetes/OpenShift deployment manifests
4. Container image in container registry
5. Serverless function implementation
6. Load balancing across multiple instances
7. Horizontal pod autoscaling (HPA)
8. High availability with multiple replicas
9. Security implementation
10. Health probes
11. Persistent storage
12. Monitoring and logging dashboard

---

**Developed for Red Hat OpenShift Hackathon**  
**Deployment Status**: ✅ Production Ready  
**Last Updated**: August 2026