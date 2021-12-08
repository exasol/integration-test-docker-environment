#!/usr/bin/env bash

#####################################################################################
###REMEMBER TO TEST ANY CHANGES HERE ON MACOSX!!!
#####################################################################################

set -euo pipefail

rl=readlink
if [[ "$(uname)" = Darwin ]]; then
  rl=greadlink
fi


if [[ ! "$(command -v $rl)" ]]; then
  echo readlink not available! Please install coreutils: On Linux \"apt-get install coreutils\" or similar. On MacOsX \"brew install coreutils\".
  exit 1
fi

SCRIPT_DIR="$(dirname "$($rl -f "${BASH_SOURCE[0]}")")"

PROJECT_ROOT_DIR="$SCRIPT_DIR/.."

IMAGE_NAME="$("$SCRIPT_DIR/construct_docker_runner_image_name.sh")"

docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_ROOT_DIR" 1>&2

echo "$IMAGE_NAME"
