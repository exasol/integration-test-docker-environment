#!/bin/bash

POETRY_INSTALL="YES"
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

source "$SCRIPT_DIR/poetry_utils.sh"

check_requirements
