#!/usr/bin/env bash
# Check the health status of the current environment
# If this script executed successfully, ware all set to run.
set -u

MAJOR_MINIMUM_VERSION_DOCKER="17"
MINOR_MINIMUM_VERSION_DOCKER="05"

help() {
  if [ "$1" == "docker" ]; then
    echo "Please follow the installation instructions on https://docs.docker.com/get-docker/"
    echo "or for a quick installation for non production linux machines the instruction on https://github.com/docker/docker-install"
  else
    echo "There is no suggestion for the issue at hand, please contact your administrator or support"
  fi
}

is_command_available () {
  command -v "$1" > /dev/null
}

is_version_compatible() {
  local min_major="$1" # $1 - expected min major version
  local min_minor="$2" # $2 - expected min minor version
  local major="$3"     # $3 - actual major version
  local minor="$4"     # $4 - actual minor version
  if [ "$major" -lt "$min_major" ]; then
    return 1
  fi
  if [ "$major" -eq "$min_major" ] && [ "$minor" -ge "$min_minor" ]; then
    return 1
  fi
  return 0
}

require() {
  # check if a command is available, otherwise print an error and exit
  if ! is_command_available "$1"; then
    echo "Could not find '$1'"
    echo
    help "$1"
    exit 1
  fi
}

check_docker_info () {
    local docker_cmd="$1"
    local details
    details=$("$docker_cmd" info)
    # we want to store the details of the command, for error reporting. Therefore we won't check within the if.
    # shellcheck disable=SC2181
    if [ "$?" -ne 0 ]; then
      echo "ERROR: Docker does not seem to be configured correctly!"
      echo "details:"
      echo "$details"
      return 1
    fi
}

docker_version () {
    local docker_cmd="$1"
    local version
    version=$("$docker_cmd" info | grep  "Server Version: " | cut -f2 -d ":" | tr -d '[:space:]')
    echo "$version"
}

docker_major_version () {
    local docker_cmd="$1"
    local version
    version=$(docker_version "$docker_cmd")
    echo "$version" | cut -f1 -d "."
}

docker_minor_version () {
    local docker_cmd="$1"
    local version
    version=$(docker_version "$docker_cmd")
    echo "$version" | cut -f2 -d "."
}

docker_check_version () {
  local docker_cmd=$1
  local actual_major_version
  actual_major_version=$(docker_major_version "$docker_cmd")
  local actual_minor_version
  actual_minor_version=$(docker_minor_version "$docker_cmd")

  if ! is_version_compatible "$MAJOR_MINIMUM_VERSION_DOCKER" "$MINOR_MINIMUM_VERSION_DOCKER" "$actual_major_version" "$actual_minor_version"; then
    echo "The currently installed docker version $actual_major_version.$actual_minor_version version is not compatible"
    help "$docker_cmd"
    return 1
  fi
}

docker_check_pull () {
  local docker_cmd=$1
  local details
  details=$("docker" pull ubuntu:18.04 2>&1)
  # We want to store the details of the command, for error reporting. Therefore we won't check within the if.
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo "Could not pull images from docker registry"
    echo "details:"
    echo "$details"
    return 1
  fi
}

docker_check_connectivity () {
  local docker_cmd=$1
  local details
  details=$(docker run --rm ubuntu:18.04 bash -c ": >/dev/tcp/1.1.1.1/53")
  # We want to store the details of the command, for error reporting. Therefore we won't check within the if.
  # shellcheck disable=SC2181
  if [ $? -ne 0 ]; then
    echo "The docker machine does not seem to have connectivity"
    echo "details:"
    echo "$details"
    return 1
  fi
}

health_check_docker () {
  local docker_cmd="docker"
  require "$docker_cmd"

  if ! check_docker_info "$docker_cmd"; then
    return 1
  fi

  if ! docker_check_version "$docker_cmd"; then
    return 1
  fi

  if ! docker_check_pull "$docker_cmd"; then
    return 1
  fi

  if ! docker_check_connectivity "$docker_cmd"; then
    return 1
  fi
}

main() {
  if [ "$1" != "run" ]; then return 0; fi
  if ! health_check_docker; then
    exit 1
  fi
}

# run all health checks
main "$1"
