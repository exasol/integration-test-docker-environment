#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

# define colors for use in output
green='\033[0;32m'
no_color='\033[0m'
grey='\033[0;90m'

echo -e "Update setup.py with dephell convert ${grey}(pre-commit hook)${no_color} "

# Jump to the current project's root directory (the one containing
# .git/)
ROOT_DIR=$(git rev-parse --show-cdup)

pushd "$ROOT_DIR" > /dev/null

rm -r exasol_integration_test_docker_environment/docker_db_config 
cp -rL docker_db_config_template exasol_integration_test_docker_environment/docker_db_config
rm -r dist
poetry build
pushd dist
tar_file=$(ls *.tar.gz)
extracted_dir=${tar_file%.tar.gz}
tar -xf $tar_file
cp "$extracted_dir/setup.py" ../setup.py
rm -r "$extracted_dir"
popd
dephell deps convert
sed -i 's/python_version = "3.6"//g' Pipfile
git add Pipfile setup.py

popd > /dev/null
