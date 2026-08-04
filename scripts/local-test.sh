#!/bin/bash

# AssetFlow Local Container Testing Script
# This script builds and tests containers locally before deploying to OpenShift

set -e

echo "🧪 Testing AssetFlow containers locally..."

# Build backend image
echo "🔨 Building backend image..."
cd backend
docker build -t assetflow-backend:test .
cd ..

# Build frontend image
echo "🔨 Building frontend image..."
cd frontend
docker build -t assetflow-frontend:test .
cd ..

# Test backend container
echo "🏃 Running backend container..."
docker run -d --name assetflow-backend-test \
  -p 8000:8000 \
  -e MONGO_URL="mongodb://localhost:27017/test" \
  -e DB_NAME="test" \
  -e JWT_SECRET="test-secret" \
  -e ENV="development" \
  assetflow-backend:test

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 10

# Test health endpoints
echo "🩺 Testing health endpoints..."
curl -f http://localhost:8000/healthz || echo "❌ Health check failed"
curl -f http://localhost:8000/readyz || echo "❌ Readiness check failed"
curl -f http://localhost:8000/startupz || echo "❌ Startup check failed"

# Stop backend container
echo "🛑 Stopping backend container..."
docker stop assetflow-backend-test
docker rm assetflow-backend-test

# Test frontend container
echo "🏃 Running frontend container..."
docker run -d --name assetflow-frontend-test \
  -p 8080:8080 \
  assetflow-frontend:test

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 5

# Test frontend
echo "🩺 Testing frontend..."
curl -f http://localhost:8080/ || echo "❌ Frontend check failed"

# Stop frontend container
echo "🛑 Stopping frontend container..."
docker stop assetflow-frontend-test
docker rm assetflow-frontend-test

echo "✅ Local container testing complete!"
