#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
# Ignore shellcheck rule here, as we want to split result by space
# shellcheck disable=SC2046
DOCKER_DBS=$(basename -a $(ls -d "${SCRIPT_DIR}/../../docker_db_config_template"/*/))


DOCKER_DBS+=($'\ndefault\n')
DOCKER_DBS+=($'7.1.0-d1\n')

printf '%s' "${DOCKER_DBS[@]}" | jq -R . | jq -cs .

