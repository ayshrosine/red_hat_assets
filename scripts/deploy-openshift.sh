#!/bin/bash

# AssetFlow OpenShift Deployment Script
# This script deploys AssetFlow to OpenShift with all required resources

set -e

# Configuration
NAMESPACE="${NAMESPACE:-assetflow}"
BACKEND_IMAGE="${BACKEND_IMAGE:-ghcr.io/ayshrosine/assetflow-backend:latest}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-ghcr.io/ayshrosine/assetflow-frontend:latest}"

echo "🚀 Deploying AssetFlow to OpenShift..."
echo "Namespace: $NAMESPACE"
echo "Backend Image: $BACKEND_IMAGE"
echo "Frontend Image: $FRONTEND_IMAGE"

# Check if logged in to OpenShift
if ! oc whoami &> /dev/null; then
    echo "❌ Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

# Create namespace if it doesn't exist
echo "📁 Creating namespace: $NAMESPACE"
oc new-project $NAMESPACE 2>/dev/null || oc project $NAMESPACE

# Create secrets from environment variables
echo "🔐 Creating secrets..."
oc create secret generic assetflow-secrets \
  --from-literal=MONGO_URL="$MONGO_URL" \
  --from-literal=JWT_SECRET="$JWT_SECRET" \
  --from-literal=GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  --from-literal=GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  --from-literal=ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  --dry-run=client -o yaml | oc apply -f -

# Apply Kubernetes manifests
echo "📦 Applying Kubernetes manifests..."
oc apply -k k8s/base

# Update images if specified
if [ "$BACKEND_IMAGE" != "ghcr.io/ayshrosine/assetflow-backend:latest" ]; then
    echo "🖼️  Updating backend image to: $BACKEND_IMAGE"
    oc set image deployment/assetflow-backend backend=$BACKEND_IMAGE
fi

if [ "$FRONTEND_IMAGE" != "ghcr.io/ayshrosine/assetflow-frontend:latest" ]; then
    echo "🖼️  Updating frontend image to: $FRONTEND_IMAGE"
    oc set image deployment/assetflow-frontend frontend=$FRONTEND_IMAGE
fi

# Wait for deployments to be ready
echo "⏳ Waiting for deployments to be ready..."
oc rollout status deployment/assetflow-backend --timeout=5m
oc rollout status deployment/assetflow-frontend --timeout=5m

# Get routes
echo "🌐 Getting routes..."
BACKEND_ROUTE=$(oc get route assetflow-backend -o jsonpath='{.spec.host}')
FRONTEND_ROUTE=$(oc get route assetflow-frontend -o jsonpath='{.spec.host}')

echo "✅ Deployment complete!"
echo ""
echo "Backend URL: https://$BACKEND_ROUTE"
echo "Frontend URL: https://$FRONTEND_ROUTE"
echo ""
echo "To check pod status:"
echo "  oc get pods"
echo ""
echo "To view logs:"
echo "  oc logs -f deployment/assetflow-backend"
echo "  oc logs -f deployment/assetflow-frontend"
