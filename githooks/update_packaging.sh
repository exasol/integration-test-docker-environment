#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

# define colors for use in output
no_color='\033[0m'
grey='\033[0;90m'

# Jump to the current project's root directory (the one containing
# .git/)
ROOT_DIR=$(git rev-parse --show-toplevel || echo)
HAS_GIT_REPO=TRUE
if [ -z "$ROOT_DIR" ]
then
  echo "Did not find git repository, using '$PWD' as ROOT_DIR"
  HAS_GIT_REPO=FALSE
  ROOT_DIR=$PWD
fi

#pushd "$ROOT_DIR" > /dev/null
pushd "$ROOT_DIR"
echo -e "Copy docker_db_config_template into package ${grey}(pre-commit hook)${no_color}"
if [ -d "exasol_integration_test_docker_environment/docker_db_config" ]
then
  rm -r "exasol_integration_test_docker_environment/docker_db_config" 
fi
cp -rL docker_db_config_template exasol_integration_test_docker_environment/docker_db_config
echo -e "Generate setup.py ${grey}(pre-commit hook)${no_color}"
if [ -d "dist" ]
then
  rm -r "dist"
fi

echo -e "Generate installer checksums ${grey}(pre-commit hook)${no_color}"
pushd starter_scripts > /dev/null
bash "$SCRIPT_DIR/create_checksums.sh"
popd > /dev/null

if [ "$HAS_GIT_REPO" == "TRUE" ]
then
  echo -e "Add generated files ${grey}(pre-commit hook)${no_color}"
  git add exasol_integration_test_docker_environment/docker_db_config starter_scripts/checksums
fi


popd > /dev/null

