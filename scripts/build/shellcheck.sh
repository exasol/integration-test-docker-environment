#!/bin/bash

set -u

interesting_paths=("starter_scripts" "scripts" "docker_db_config_template" "exasol_integration_test_docker_environment")

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
status=0

for path in "${interesting_paths[@]}"; do
  find "$SCRIPT_DIR/../../$path" -name '*.sh' -type f -print0 | xargs -0 -n1 shellcheck -x
  test $? -ne 0 && status=1
done


interesting_files=("./start-test-env")

for f in "${interesting_files[@]}"; do
  shellcheck -x "$SCRIPT_DIR/../../$f"
  test $? -ne 0 && status=1
done

exit "$status"
