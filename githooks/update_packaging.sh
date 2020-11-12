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
ROOT_DIR=$(git rev-parse --show-cdup)

pushd "$ROOT_DIR" > /dev/null
echo -e "Copy docker_db_config_template into package ${grey}(pre-commit hook)${no_color}"
rm -r exasol_integration_test_docker_environment/docker_db_config 
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
echo -e "Generate Pipfile ${grey}(pre-commit hook)${no_color}"
dephell deps convert > /dev/null
sed -i 's/python_version = "3.6"//g' Pipfile
echo -e "Add generated files ${grey}(pre-commit hook)${no_color}"
git add Pipfile setup.py exasol_integration_test_docker_environment/docker_db_config

popd > /dev/null
