#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

GIT_IMAGE_NAME=$("$SCRIPT_DIR/construct_docker_runner_image_name.sh")

docker push "$GIT_IMAGE_NAME"

LATEST_IMAGE_NAME=$("$SCRIPT_DIR/construct_docker_runner_image_name.sh" latest)

docker tag "$GIT_IMAGE_NAME" "$LATEST_IMAGE_NAME"

docker push "$LATEST_IMAGE_NAME"
