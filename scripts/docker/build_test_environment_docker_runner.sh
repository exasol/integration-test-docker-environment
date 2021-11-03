#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

IMAGE_NAME="$($SCRIPT_DIR/construct_docker_runner_image_name.sh)"

docker build -t $IMAGE_NAME $SCRIPT_DIR/../..
