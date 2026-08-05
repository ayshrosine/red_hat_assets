#!/bin/bash

# Build and push AssetFlow images to GitHub Container Registry

echo "🔨 Building and pushing AssetFlow images to GitHub Container Registry..."

# Login to GitHub Container Registry
echo "🔐 Logging in to GitHub Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u ayshrosine --password-stdin

# Build and push backend
echo "🔨 Building backend image..."
cd backend
docker build -t ghcr.io/ayshrosine/assetflow-backend:latest .
echo "📤 Pushing backend image..."
docker push ghcr.io/ayshrosine/assetflow-backend:latest
cd ..

# Build and push frontend
echo "🔨 Building frontend image..."
cd frontend
docker build -t ghcr.io/ayshrosine/assetflow-frontend:latest .
echo "📤 Pushing frontend image..."
docker push ghcr.io/ayshrosine/assetflow-frontend:latest
cd ..

echo "✅ Images built and pushed successfully!"
echo ""
echo "Now update the OpenShift deployments:"
echo "  oc set image deployment/assetflow-backend backend=ghcr.io/ayshrosine/assetflow-backend:latest"
echo "  oc set image deployment/assetflow-frontend frontend=ghcr.io/ayshrosine/assetflow-frontend:latest"
