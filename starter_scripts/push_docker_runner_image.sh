#!/usr/bin/env bash

set -euo pipefail

# If there is at least one argument, we create one docker tag with suffix=$argument per argument
# If there is no argument given we create one docker tag with suffix "latest"
if [ -n "${1-}" ]; then
  image_suffixes=("$@")
else
  image_suffixes=("latest")
fi

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

GIT_IMAGE_NAME="$("$SCRIPT_DIR/build_docker_runner_image.sh")"

docker push "$GIT_IMAGE_NAME"

for image_suffix in "${image_suffixes[@]}"; do

  RENAMED_IMAGE_NAME="$("$SCRIPT_DIR/construct_docker_runner_image_name.sh" "$image_suffix")"

  docker tag "$GIT_IMAGE_NAME" "$RENAMED_IMAGE_NAME"

  docker push "$RENAMED_IMAGE_NAME"

done