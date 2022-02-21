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
  # $1 - expected major version
  # $2 - expected minor version
  # $3 - actual major version
  # $4 - actual minor version
  if [ "$3" -lt "$1" ]; then
    return 1
  fi
  if [ "$3" -eq "$1" ] && [ "$4" -ge "$2" ]; then
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


docker_version () {
    local docker_cmd="$1"
    local version=$("$docker_cmd" info | grep  "Server Version: " | cut -f2 -d ":" | tr -d '[:space:]')
    echo "$version"
}

docker_major_version () {
    local docker_cmd="$1"
    local version=$(docker_version "$docker_cmd")
    echo "$version" | cut -f1 -d "."
}

docker_minor_version () {
    local docker_cmd="$1"
    local version=$(docker_version "$docker_cmd")
    echo "$version" | cut -f2 -d "."
}


check_docker_pull () {
    docker pull ubuntu:18.04fff 2>&1
    if [ "$?" -eq 0 ]; then
      return 0
    fi
        return 1
}

check_docker_connectivity () {
  local docker_internet_test_run=$(docker run --rm ubuntu:18.04 bash -c ": >/dev/tcp/1.1.1.1/53")
  if [ ! "$?" ]; then
      return 1
  fi
  return 0
}


health_check_docker () {
  local docker_cmd="docker"
  require "$docker_cmd"

  # check docker version
  local actual_major_version=$(docker_major_version "$docker_cmd")
  local actual_minor_version=$(docker_minor_version "$docker_cmd")
  if ! is_version_compatible "$MAJOR_MINIMUM_VERSION_DOCKER" "$MINOR_MINIMUM_VERSION_DOCKER" "$actual_major_version" "$actual_minor_version"; then
    echo "The currently installed docker version $actual_major_version.$actual_minor_version version is not compatible"
    help "$docker_cmd"
    return 1
  fi

  # can't be made local, otherwise it will eat the last return code
  details=$("docker" pull ubuntu:18.04 2>&1)
  if [ "$?" -ne 0 ]; then
    echo "Could not pull images from docker registry"
    echo "details:"
    echo "$details"
    return 1
  fi

  # can't be made local, otherwise it will eat the last return code
  details=$(docker run --rm ubuntu:18.04 bash -c ": >/dev/tcp/1.1.1.1/53")
  if [ "$?" -ne 0 ]; then
    echo "The docker machine does not seem to have connectivity"
    echo "details:"
    echo "$details"
    return 1
  fi
  return 0
}

main() {
  if ! health_check_docker; then
    exit 1
  fi
  exit 0
}

# run all health checks
main
