#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

# define colors for use in output
green='\033[0;32m'
no_color='\033[0m'
grey='\033[0;90m'

# Jump to the current project's root directory (the one containing
# .git/)
ROOT_DIR=$(git rev-parse --show-cdup || echo)
NO_GIT=FALSE
if [ -z "$ROOT_DIR" ]
then
  echo "Did not found git repository, using '$PWD' as ROOT_DIR"
  NO_GIT=TRUE
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
poetry build > /dev/null
pushd dist > /dev/null
tar_file=$(ls *.tar.gz)
extracted_dir=${tar_file%.tar.gz}
tar -xf $tar_file
cp "$extracted_dir/setup.py" ../setup.py
rm -r "$extracted_dir"
popd > /dev/null

if [ "$NO_GIT" == "FALSE" ]
then
  echo -e "Add generated files ${grey}(pre-commit hook)${no_color}"
  git add setup.py exasol_integration_test_docker_environment/docker_db_config
fi

popd > /dev/null
