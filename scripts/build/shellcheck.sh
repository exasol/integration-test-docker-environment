#!/bin/bash

set -euo pipefail

interesting_paths=("scripts" "docker_db_config_template" "exasol_integration_test_docker_environment" "githooks")

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

for path in "${interesting_paths[@]}"; do
  find "$SCRIPT_DIR/../../$path" -name '*.sh' -type f -print0 | xargs -0 -n1 shellcheck -x
done


interesting_files=("./start-test-env" "./start-test-env-with-poetry" "./start-test-env-without-poetry")

for f in "${interesting_files[@]}"; do
  shellcheck -x "$SCRIPT_DIR/../../$f"
done
