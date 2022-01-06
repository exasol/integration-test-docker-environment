#!/bin/bash 
   

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" 

#shellcheck source=./scripts/build/poetry_utils.sh
source "$SCRIPT_DIR/poetry_utils.sh"

check_requirements

set -euo pipefail

init_poetry

if [ -n "$POETRY_BIN" ]
then
  PYTHONPATH=. $POETRY_BIN build
else
  echo "Could not find poetry!"
  exit 1
fi

