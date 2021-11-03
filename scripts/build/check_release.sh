#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" 
 
latast_git_tag=$(git log --no-walk --tags --pretty=format:'%d' --abbrev-commit | grep -Eo 'tag: [0-9]+.[0-9]+.[0-9]+' | cut -d " " -f 2 | head -n 1)
latest_poetry_version=$(cat pyproject.toml | grep -Eo 'version = \"[0-9]+.[0-9]+.[0-9]+\"' | grep -Eo "[0-9]+.[0-9]+.[0-9]+")

if [[ -z $latast_git_tag ]]; then
  echo "Could not find latest git tag."
  exit 1
fi

if [[ -z $latest_poetry_version ]]; then
  echo "Could not read poetry version."
  exit 1
fi

echo "POETRY VERSION: $latest_poetry_version"
echo "GIT TAG: $latast_git_tag"
if [[ $latast_git_tag == $latest_poetry_version ]]; then
  echo "Poetry version is not updated!"
  exit 1
fi
