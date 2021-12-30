#!/bin/bash

#shellcheck disable=SC2034
POETRY_INSTALL="YES"
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

#shellcheck source=./scripts/build/poetry_utils.sh
source "$SCRIPT_DIR/poetry_utils.sh"

check_requirements
