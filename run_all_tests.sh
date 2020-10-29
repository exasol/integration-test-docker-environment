#!/bin/bash 
   
COMMAND_LINE_ARGS=$* 
SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" 
 
source pipenv_utils.sh 
 
discover_pipenv 
init_pipenv "$PIPENV_BIN" 

if [ -n "$PIPENV_BIN" ]
then
  PYTHONPATH=. $PIPENV_BIN run python3 -m unittest discover exasol_integration_test_docker_environment/test
else
  echo "Could not find pipenv!"
  exit 1
fi

