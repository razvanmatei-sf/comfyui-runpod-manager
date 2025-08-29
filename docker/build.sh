#!/bin/bash

# GitHub Container Registry configuration
GHCR_IMAGE="ghcr.io/razvanmatei-sf/comfyui-admin"
TAG="latest"

echo "Building Docker image for linux/amd64: ${GHCR_IMAGE}:${TAG}"

# Build and push to GitHub Container Registry in one step
docker buildx build --platform linux/amd64 -t ${GHCR_IMAGE}:${TAG} --push .

if [ $? -eq 0 ]; then
    echo "✅ Build and push successful!"
    echo "Image available at: ${GHCR_IMAGE}:${TAG}"
    echo ""
    echo "🚀 Use this image in RunPod:"
    echo "${GHCR_IMAGE}:${TAG}"
else
    echo "❌ Build failed!"
    echo ""
    echo "Make sure you're logged into GitHub Container Registry:"
    echo "echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u razvanmatei-sf --password-stdin"
    exit 1
fi

echo ""
echo "To run locally for testing:"
echo "docker run -p 8080:8080 -p 8188:8188 -p 8888:8888 -v \$(pwd)/workspace:/workspace ${GHCR_IMAGE}:${TAG}"