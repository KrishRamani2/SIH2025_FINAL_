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
INCLUDE_TTP_LINUX="false"
INCLUDE_TTP_NGINX="false"
INCLUDE_TTP_WINDOWS="false"
TAG_SUFFIX=""
for arg in "$@"
do
    case $arg in
      --linux)
      INCLUDE_LINUX="true"
      INCLUDE_TTP_LINUX="true"
      TAG_SUFFIX+="-linux"
      shift
      ;;
      --nginx)
      INCLUDE_NGINX="true"
      INCLUDE_TTP_NGINX="true"
      TAG_SUFFIX+="-nginx"
      shift
      ;;
      --windows)
      INCLUDE_WINDOWS="true"
      INCLUDE_TTP_WINDOWS="true"
      TAG_SUFFIX+="-windows"
      shift
      ;;
      --all)
      INCLUDE_LINUX="true"
      INCLUDE_NGINX="true"
      INCLUDE_WINDOWS="true"
      INCLUDE_TTP_LINUX="true"
      INCLUDE_TTP_NGINX="true"
      INCLUDE_TTP_WINDOWS="true"
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
export INCLUDE_LINUX=$INCLUDE_LINUX
export INCLUDE_NGINX=$INCLUDE_NGINX
export INCLUDE_WINDOWS=$INCLUDE_WINDOWS
export INCLUDE_TTP_LINUX=$INCLUDE_TTP_LINUX
export INCLUDE_TTP_NGINX=$INCLUDE_TTP_NGINX
export INCLUDE_TTP_WINDOWS=$INCLUDE_TTP_WINDOWS
export IMAGE_TAG=$IMAGE_TAG

# Run docker-compose build
docker-compose build

echo "--- Build Complete ---"
echo "To run this container, use docker-compose up -d"
echo "Or use the specific image: docker run -d --rm <ports> sih-central-custom:$IMAGE_TAG"
