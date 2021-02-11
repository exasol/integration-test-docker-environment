#!/bin/bash 
   
COMMAND_LINE_ARGS=("${@}") 
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" 
 
source "$SCRIPT_DIR/poetry_utils.sh"

check_requirements

set -euo pipefail

init_poetry

if [ -n "$POETRY_BIN" ]
then
  PYTHONPATH=. $POETRY_BIN run python3 -m unittest discover exasol_integration_test_docker_environment/test
else
  echo "Could not find poetry!"
  exit 1
fi

