# AssetFlow OpenShift Hackathon - Live Demonstration Script

## Overview

**Total Duration**: 10-12 minutes
**Target Audience**: Hackathon judges and technical evaluators
**Goal**: Demonstrate all 12 deliverables in a cohesive, professional presentation

## Pre-Demo Preparation (10 minutes before start)

### Environment Setup
- [ ] Open OpenShift Console in browser (logged in)
- [ ] Open GitHub repository in separate tab
- [ ] Open terminal with oc CLI connected to cluster
- [ ] Verify all pods are running: `oc get pods`
- [ ] Prepare load testing tool (Apache Bench or similar)
- [ ] Open frontend URL in browser (ready to show)
- [ ] Open backend URL in browser (ready to test)
- [ ] Navigate to OpenShift Observe tab (ready to show monitoring)

### Backup Plans
- [ ] Have terminal commands ready in text file
- [ ] Know pod names for quick log access
- [ ] Have rollback command ready: `oc rollout undo deployment/assetflow-backend`
- [ ] Have secret names handy for demonstration

---

## Demo Script

### Section 1: Introduction and Architecture Overview (2 minutes)

**Time**: 0:00 - 2:00

**Speaker Notes**:
"Good morning/afternoon. Today I'll be demonstrating AssetFlow, a comprehensive asset management system deployed on Red Hat OpenShift. This project showcases modern cloud-native practices including microservices architecture, serverless computing, and GitOps-based continuous deployment."

**Key Points to Cover**:
1. **Project Overview**: Asset management system with asset tracking, booking, maintenance scheduling
2. **Architecture**: FastAPI backend, React frontend, MongoDB Atlas database
3. **OpenShift Features**: Demonstrates Kubernetes/OpenShift capabilities for enterprise applications
4. **Deliverables**: All 12 hackathon requirements implemented

**Visual Aids**:
- Show GitHub repository structure
- Show high-level architecture diagram (if available)
- Display OpenShift console overview

**Commands/Actions**:
```bash
# Show repository structure
git ls-files | head -20

# Show OpenShift project overview
oc get all
```

**Expected Outcome**: Judges understand the project scope and technical approach

---

### Section 2: Git Repository and CI/CD Walkthrough (3 minutes)

**Time**: 2:00 - 5:00

**Speaker Notes**:
"The project follows GitOps best practices with all infrastructure defined as code. Let me show you the repository structure and our CI/CD pipeline that automates the entire build and deployment process."

**Key Points to Cover**:
1. **Repository Structure**: Backend, frontend, Kubernetes manifests, CI/CD workflows
2. **Security**: No credentials in code, proper .gitignore, secret templates
3. **CI/CD Pipeline**: GitHub Actions workflow that builds, tests, and deploys
4. **Automated Deployment**: Pipeline pushes to OpenShift on every commit

**Visual Aids**:
- Show GitHub repository with directory structure
- Display .github/workflows/ci-cd.yaml
- Show GitHub Actions workflow runs (if available)
- Display secret-template.yaml with placeholders

**Commands/Actions**:
```bash
# Show repository structure
git ls-files
git log --oneline -5

# Show CI/CD workflow
cat .github/workflows/ci-cd.yaml

# Show security practices
cat .gitignore
cat k8s/base/secret-template.yaml
```

**Expected Outcome**: Judges see proper GitOps practices and automated deployment pipeline

---

### Section 3: Kubernetes/OpenShift Manifests Explanation (2 minutes)

**Time**: 5:00 - 7:00

**Speaker Notes**:
"Our deployment is fully defined as code using Kubernetes/OpenShift manifests. Let me walk you through the key resources that demonstrate the platform's capabilities."

**Key Points to Cover**:
1. **Deployment Manifests**: Backend and frontend deployments with resource limits
2. **Services and Routes**: Internal load balancing and external HTTPS access
3. **Configuration**: ConfigMaps and Secrets for environment-specific configuration
4. **Security**: RBAC, Network Policies, and TLS configuration

**Visual Aids**:
- Show k8s/base/ directory structure
- Display backend-deployment.yaml (highlight replicas, resources, health probes)
- Display networkpolicy.yaml (show security rules)
- Display rbac.yaml (show least-privilege access)

**Commands/Actions**:
```bash
# Show all Kubernetes resources
oc get all
oc get configmaps
oc get secrets
oc get networkpolicy
oc get hpa

# Show deployment details
oc describe deployment assetflow-backend
oc describe deployment assetflow-frontend
```

**Expected Outcome**: Judges understand the infrastructure-as-code approach and OpenShift capabilities

---

### Section 4: Live Deployment Demonstration (3 minutes)

**Time**: 7:00 - 10:00

**Speaker Notes**:
"Now let me show you the live deployment. All resources are currently running in this OpenShift cluster, demonstrating the platform's ability to host complex applications."

**Key Points to Cover**:
1. **Pod Status**: All pods running and healthy
2. **Service Endpoints**: Load balancing across multiple instances
3. **Routes**: HTTPS access with TLS termination
4. **Health Checks**: Application health monitoring

**Visual Aids**:
- Show OpenShift Console → Administrator → Workloads → Pods
- Show pod status and health indicators
- Display service endpoints
- Show route configuration

**Commands/Actions**:
```bash
# Show pod status
oc get pods
oc describe pod <backend-pod-name>

# Show service endpoints
oc get endpoints assetflow-backend
oc get endpoints assetflow-frontend

# Show routes
oc get routes
oc describe route assetflow-frontend

# Test health endpoints
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/healthz
curl https://assetflow-backend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com/readyz
```

**Expected Outcome**: Judges see live, running deployment with healthy pods and working services

---

### Section 5: Health Probes and Monitoring Demo (2 minutes)

**Time**: 10:00 - 12:00

**Speaker Notes**:
"OpenShift provides comprehensive monitoring capabilities. Let me demonstrate the health probes we've configured and the built-in monitoring dashboard."

**Key Points to Cover**:
1. **Health Probes**: Liveness, readiness, and startup probes
2. **Monitoring Dashboard**: OpenShift Observe tab with metrics
3. **Log Aggregation**: Centralized logging with OpenShift
4. **Resource Monitoring**: CPU, memory, and network metrics

**Visual Aids**:
- Navigate to OpenShift Console → Observe → Metrics
- Show CPU/memory utilization graphs
- Show pod health status
- Display application logs

**Commands/Actions**:
```bash
# Show health probe configuration
oc describe deployment assetflow-backend | grep -A 20 "Probe"

# Test health endpoints
curl https://assetflow-backend-.../healthz
curl https://assetflow-backend-.../readyz
curl https://assetflow-backend-.../startupz

# View resource metrics
oc top pods
oc top nodes

# View logs
oc logs -l app=assetflow-backend --tail=20
```

**Expected Outcome**: Judges see comprehensive monitoring and health checking capabilities

---

### Section 6: Load Balancing and Autoscaling Demo (3 minutes)

**Time**: 12:00 - 15:00

**Speaker Notes**:
"One of OpenShift's key strengths is its ability to handle load through horizontal scaling. Let me demonstrate load balancing and automatic scaling based on CPU utilization."

**Key Points to Cover**:
1. **Load Balancing**: Service-based load distribution across pods
2. **Horizontal Pod Autoscaler**: CPU-based automatic scaling
3. **Current Metrics**: Show current CPU utilization and replica count
4. **Scaling Demo**: Generate load to trigger autoscaling

**Visual Aids**:
- Show HPA configuration and current status
- Display current CPU utilization
- Generate load with Apache Bench
- Watch HPA scale up pods

**Commands/Actions**:
```bash
# Show HPA configuration
oc get hpa
oc describe hpa assetflow-backend-hpa

# Show current metrics
oc top pods

# Generate load to trigger autoscaling
ab -n 1000 -c 10 https://assetflow-backend-.../healthz

# Watch HPA scale up
watch oc get hpa
watch oc get pods
```

**Expected Outcome**: Judges see automatic scaling in response to increased load

---

### Section 7: Security Features Demonstration (2 minutes)

**Time**: 15:00 - 17:00

**Speaker Notes**:
"Security is paramount in cloud deployments. Our implementation demonstrates OpenShift's comprehensive security features including TLS, RBAC, Network Policies, and Secrets management."

**Key Points to Cover**:
1. **TLS/SSL**: HTTPS with edge termination
2. **Secrets Management**: Kubernetes Secrets for sensitive data
3. **RBAC**: Service accounts with least-privilege access
4. **Network Policies**: Default-deny with explicit allow rules

**Visual Aids**:
- Show route TLS configuration
- Display secret (non-sensitive parts only)
- Show RBAC configuration
- Display network policy rules

**Commands/Actions**:
```bash
# Show TLS configuration
oc describe route assetflow-frontend
oc describe route assetflow-backend

# Show secrets (without revealing values)
oc get secrets
oc describe secret assetflow-secrets

# Show RBAC
oc get serviceaccounts
oc get roles
oc describe role assetflow-pod-reader

# Show network policies
oc get networkpolicy
oc describe networkpolicy default-deny-all
```

**Expected Outcome**: Judges see comprehensive security implementation

---

### Section 8: Serverless Function Demo (2 minutes)

**Time**: 17:00 - 19:00

**Speaker Notes**:
"We've implemented a serverless reminder function using Knative, demonstrating event-driven architecture. This function automatically sends notifications for overdue asset maintenance."

**Key Points to Cover**:
1. **Knative Service**: Serverless deployment model
2. **Event Trigger**: PingSource for cron-based scheduling
3. **Scaling to Zero**: Serverless function scales to zero when not in use
4. **Event-Driven**: Replaces traditional polling approach

**Visual Aids**:
- Show Knative service configuration
- Display PingSource cron trigger
- Show function logs
- Demonstrate scaling behavior

**Commands/Actions**:
```bash
# Show Knative service
oc get ksvc
oc describe ksvc assetflow-reminder-service

# Show PingSource
oc get pingsources
oc describe pingsource assetflow-reminder-ping

# View function logs
oc logs -l serving.knative.dev/service=assetflow-reminder-service

# Show scaling behavior
oc get pods -l serving.knative.dev/service=assetflow-reminder-service
```

**Expected Outcome**: Judges see serverless architecture and event-driven processing

---

### Section 9: Persistent Storage Demo (2 minutes)

**Time**: 19:00 - 21:00

**Speaker Notes**:
"For file upload functionality, we've implemented persistent storage using Kubernetes Persistent Volume Claims. Let me show you our storage architecture and the dedicated storage demonstration deployment."

**Key Points to Cover**:
1. **PVC Configuration**: Persistent volume claim for file storage
2. **Storage Demo Deployment**: Dedicated single-replica deployment for storage demo
3. **Main Deployment Architecture**: Ephemeral storage for high availability
4. **File Upload Functionality**: Working upload feature with persistence

**Visual Aids**:
- Show PVC status and configuration
- Display storage demo deployment
- Show volume mount configuration
- Demonstrate file upload

**Commands/Actions**:
```bash
# Show PVC
oc get pvc
oc describe pvc assetflow-uploads-pvc

# Show storage demo deployment
oc get deployment assetflow-backend-storage-demo
oc describe deployment assetflow-backend-storage-demo

# Test file upload
curl -X POST -F "file=@test.txt" https://assetflow-backend-.../uploads

# Verify persistence
oc describe pod <storage-demo-pod-name>
```

**Expected Outcome**: Judges see persistent storage implementation and architecture decision

---

### Section 10: Rolling Update and High Availability Demo (3 minutes)

**Time**: 21:00 - 24:00

**Speaker Notes**:
"High availability is critical for production applications. Let me demonstrate zero-downtime rolling updates and our Pod Disruption Budget that ensures availability during maintenance."

**Key Points to Cover**:
1. **Rolling Update Strategy**: Zero-downtime deployment updates
2. **Pod Disruption Budget**: Ensures minimum available pods
3. **Live Update**: Trigger a rolling update during demo
4. **Availability Verification**: Show continuous service during update

**Visual Aids**:
- Show deployment strategy configuration
- Display PDB configuration
- Trigger rolling update
- Monitor continuous service availability

**Commands/Actions**:
```bash
# Show rolling update strategy
oc describe deployment assetflow-backend | grep -A 5 "Strategy"

# Show PDB
oc get poddisruptionbudget
oc describe pdb assetflow-backend-pdb

# Trigger rolling update
oc set image deployment/assetflow-backend backend=ghcr.io/ayshrosine/assetflow-backend:latest

# Monitor rollout with continuous testing
oc rollout status deployment/assetflow-backend &
while true; do curl https://assetflow-backend-.../healthz; sleep 1; done
```

**Expected Outcome**: Judges see zero-downtime deployment and high availability

---

### Section 11: Frontend Application Demo (3 minutes)

**Time**: 24:00 - 27:00

**Speaker Notes**:
"Now let me show you the actual application. The frontend is a React application that provides a user-friendly interface for asset management, fully integrated with our backend APIs."

**Key Points to Cover**:
1. **Login Page**: Google OAuth authentication
2. **Dashboard**: Asset overview and management
3. **User Interface**: Modern, responsive design
4. **API Integration**: Seamless backend communication

**Visual Aids**:
- Open frontend URL in browser
- Show login page with Google OAuth
- Demonstrate dashboard functionality
- Show API calls in browser dev tools

**Commands/Actions**:
```bash
# Show frontend URL
oc get route assetflow-frontend

# Open in browser
# Navigate to: https://assetflow-frontend-ayshrosine-dev.apps.rm1.0a51.p1.openshiftapps.com

# Demonstrate:
# - Google OAuth login
# - Dashboard navigation
# - Asset management features
# - API calls in Network tab
```

**Expected Outcome**: Judges see working application with modern UI

---

### Section 12: Q&A and Summary (3 minutes)

**Time**: 27:00 - 30:00

**Speaker Notes**:
"That concludes our demonstration of AssetFlow on OpenShift. We've successfully implemented all 12 hackathon deliverables showcasing enterprise-grade cloud-native application deployment."

**Key Points to Cover**:
1. **Deliverables Summary**: All 12 requirements met
2. **Technical Highlights**: Microservices, serverless, GitOps, security
3. **OpenShift Benefits**: Platform capabilities demonstrated
4. **Future Enhancements**: Potential improvements and scaling

**Visual Aids**:
- Display deliverables checklist
- Show architecture summary
- Display metrics/achievements

**Commands/Actions**:
```bash
# Final system check
oc get pods
oc get all
oc top pods

# Show final status
echo "All systems operational"
```

**Expected Outcome**: Judges have comprehensive understanding of project and Q&A

---

## Backup Demonstrations

### If Load Balancing Demo Fails
```bash
# Manual load distribution test
for i in {1..10}; do
  curl https://assetflow-backend-.../healthz
  echo "--- Request $i ---"
done
```

### If Autoscaling Demo Fails
```bash
# Manual scaling demonstration
oc scale deployment assetflow-backend --replicas=4
oc get pods
oc scale deployment assetflow-backend --replicas=2
```

### If Rolling Update Demo Fails
```bash
# Show update strategy instead
oc describe deployment assetflow-backend | grep -A 10 "Strategy"
oc rollout history deployment/assetflow-backend
```

### If Serverless Demo Fails
```bash
# Show configuration instead
oc get ksvc assetflow-reminder-service -o yaml
oc get pingsources -o yaml
```

---

## Technical Requirements for Demo

### System Requirements
- OpenShift Console access (web browser)
- oc CLI installed and configured
- Terminal with command access
- Internet connectivity for external routes
- GitHub repository access

### Software Requirements
- Web browser (Chrome/Firefox recommended)
- Terminal application
- oc CLI tool
- curl (for API testing)
- Apache Bench (ab) for load testing

### Account Requirements
- OpenShift cluster access
- GitHub account (for repository viewing)
- Google account (for OAuth demo)

---

## Troubleshooting During Demo

### Common Issues and Solutions

#### Pods Not Running
```bash
# Check pod status
oc get pods
oc describe pod <failing-pod>

# Check logs
oc logs <failing-pod>

# Common fixes
oc delete pod <stuck-pod>  # Let it recreate
oc rollout restart deployment/assetflow-backend
```

#### Routes Not Accessible
```bash
# Check route status
oc get routes
oc describe route assetflow-frontend

# Check service endpoints
oc get endpoints assetflow-frontend

# Verify DNS resolution
nslookup assetflow-frontend-...apps.openshiftapps.com
```

#### HPA Not Scaling
```bash
# Check HPA status
oc get hpa
oc describe hpa assetflow-backend-hpa

# Check metrics server
oc top pods

# Manual scaling as fallback
oc scale deployment assetflow-backend --replicas=4
```

#### Authentication Issues
```bash
# Check secrets
oc get secrets
oc describe secret assetflow-secrets

# Verify Google OAuth configuration
# Check Google Console settings
# Verify authorized origins
```

---

## Post-Demo Cleanup

### Reset to Baseline State
```bash
# Scale back to normal levels
oc scale deployment assetflow-backend --replicas=2
oc scale deployment assetflow-frontend --replicas=2

# Clean up test resources
oc delete pod <test-pods>

# Verify system state
oc get pods
oc get all
```

### Documentation Updates
- Update demo script with any issues encountered
- Note any questions asked during Q&A
- Document successful demonstrations
- Record any technical issues resolved

---

## Success Criteria

### Demo Success Indicators
- ✅ All 12 deliverables demonstrated
- ✅ No technical failures during demo
- ✅ All commands execute successfully
- ✅ Application fully functional
- ✅ Judges engaged and asking questions
- ✅ Time management within 30 minutes

### Technical Validation
- ✅ All pods running and healthy
- ✅ All services accessible
- ✅ Monitoring dashboards functional
- ✅ Security features demonstrated
- ✅ Autoscaling behavior observed
- ✅ Rolling updates successful

---

## Additional Resources

### Documentation Links
- VERIFICATION_CHECKLIST.md - Detailed verification procedures
- TROUBLESHOOTING_GUIDE.md - Common issues and solutions
- MONITORING_GUIDE.md - OpenShift monitoring usage
- TEST_SCENARIOS.md - Detailed test procedures
- AssetFlow-OpenShift-Hackathon-Guide.md - Implementation guide

### Quick Reference Commands
```bash
# System status
oc get pods
oc get all
oc top pods

# Application access
oc get routes
curl https://assetflow-frontend-.../
curl https://assetflow-backend-.../healthz

# Monitoring
oc logs -l app=assetflow-backend
oc describe pod <pod-name>

# Scaling
oc scale deployment assetflow-backend --replicas=4
oc get hpa
```

---

## Conclusion

This demo script provides a comprehensive, professional demonstration of all 12 hackathon deliverables. The script is designed to be flexible, allowing for adjustments based on time constraints and technical conditions. Each section includes backup plans and troubleshooting guidance to ensure a successful presentation.

**Estimated Total Time**: 27-30 minutes (including Q&A)
**Technical Complexity**: Advanced
**Success Rate**: High (with proper preparation and backup plans)