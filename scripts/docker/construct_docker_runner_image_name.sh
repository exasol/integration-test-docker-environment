#!/usr/bin/env bash

set -euo pipefail

if [ -z "${1-}" ]
then
  VERSION="$(git rev-parse HEAD || echo latest)"
else
  VERSION="$1"
fi

echo "exatk/integration_test_docker_environment_runner:$VERSION"
