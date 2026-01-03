#!/bin/bash

# This script builds a basic Docker image with ALL Sigma rules.
# For custom rule selection, use build-compose.sh instead.
# Usage: ./build.sh

IMAGE_NAME="sih-central-custom"
IMAGE_TAG="latest"

# Check if user passed arguments (they should use build-compose.sh instead)
if [ $# -gt 0 ]; then
    echo "Warning: build.sh ignores arguments. Use build-compose.sh for custom builds."
    echo "Example: ./build-compose.sh --linux --nginx"
    echo "Continuing with full build..."
fi

echo "Building Docker image: $IMAGE_NAME:$IMAGE_TAG (with ALL rules)"

docker build -t "$IMAGE_NAME:$IMAGE_TAG" .

echo "Build complete."
echo "To run: docker run -d -p 8000:8000 -p 5140:5140/udp $IMAGE_NAME:$IMAGE_TAG"
