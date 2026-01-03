#!/bin/bash

# This script builds a custom Docker image using docker-compose.
# You can specify which sets of Sigma rules to include in the final image.
# Example usage:
# ./build-compose.sh --linux --nginx
# ./build-compose.sh --windows
# ./build-compose.sh --all
# ./build-compose.sh (builds a base image with no rules)

# --- Defaults ---
INCLUDE_LINUX="false"
INCLUDE_NGINX="false"
INCLUDE_WINDOWS="false"
TAG_SUFFIX=""

# --- Parse Command-Line Arguments ---
for arg in "$@"
do
    case $arg in
        --linux)
        INCLUDE_LINUX="true"
        TAG_SUFFIX+="-linux"
        shift
        ;;
        --nginx)
        INCLUDE_NGINX="true"
        TAG_SUFFIX+="-nginx"
        shift
        ;;
        --windows)
        INCLUDE_WINDOWS="true"
        TAG_SUFFIX+="-windows"
        shift
        ;;
        --all)
        INCLUDE_LINUX="true"
        INCLUDE_NGINX="true"
        INCLUDE_WINDOWS="true"
        TAG_SUFFIX="-all"
        shift
        ;;
    esac
done

# If no rules are selected, we'll call the tag 'base'
if [ -z "$TAG_SUFFIX" ]; then
  IMAGE_TAG="base"
else
  # Remove leading hyphen from the tag
  IMAGE_TAG=${TAG_SUFFIX#-}
fi

echo "--- Building Docker Image ---"
echo "Image Tag: sih-central-custom:$IMAGE_TAG"
echo "Including Linux rules: $INCLUDE_LINUX"
echo "Including Nginx rules: $INCLUDE_NGINX"
echo "Including Windows rules: $INCLUDE_WINDOWS"
echo "-----------------------------"

# Export variables for docker-compose to read
export INCLUDE_LINUX_RULES=$INCLUDE_LINUX
export INCLUDE_NGINX_RULES=$INCLUDE_NGINX
export INCLUDE_WINDOWS_RULES=$INCLUDE_WINDOWS
export IMAGE_TAG=$IMAGE_TAG

# Run docker-compose build
docker-compose build

echo "--- Build Complete ---"
echo "To run this container, use docker-compose up -d"
echo "Or use the specific image: docker run -d --rm <ports> sih-central-custom:$IMAGE_TAG"
