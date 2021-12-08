#!/usr/bin/env bash


SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

#shellcheck source=./scripts/build/poetry_utils.sh
source "$SCRIPT_DIR/scripts/build/poetry_utils.sh"

check_requirements

set -euo pipefail

init_poetry

if [ -n "$POETRY_BIN" ]
then
  export PYTHONPATH="$SCRIPT_DIR"
  $POETRY_BIN run bash "$SCRIPT_DIR/exaslct_without_poetry.sh" "${@}"
else
  echo "Could not find poetry!"
  exit 1
fi
