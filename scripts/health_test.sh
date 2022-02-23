#!/bin/bash
# file: scripts/health_test.sh
# Attention:
#  * This test uses [shunit2](https://github.com/kward/shunit2)
#  * It assumes it is executed from the project root like this
#    shunit2 scripts/health_test.sh
#
. ./scripts/health.sh

test_is_version_compatible_invalid_major_version() {
  local major="1"
  local minor="1"
  local min_major="2"
  local min_minor="1"
  assertFalse "required: >= ${min_major}.${min_minor}, actual: ${major}.${minor}"\
    "is_version_compatible ${min_major} ${min_minor} ${major} ${minor}"
}

test_is_version_compatible_invalid_minor_version() {
  local major="1"
  local minor="1"
  local min_major="1"
  local min_minor="0"
  assertFalse "required: >= ${min_major}.${min_minor}, actual: ${major}.${minor}"\
    "is_version_compatible ${min_major} ${min_minor} ${major} ${minor}"
}

test_is_version_compatible_valid_version() {
  local major="2"
  local minor="10"
  local min_major="1"
  local min_minor="2"
  assertTrue "required: >= ${min_major}.${min_minor}, actual: ${major}.${minor}"\
    "is_version_compatible ${min_major} ${min_minor} ${major} ${minor}"
}

test_is_command_available_returns_false_if_command_is_not_available() {
  assertFalse "is_command_available 'UnknownCommandXYZ'"
}

test_is_command_available_returns_true_if_command_is_available() {
  assertTrue "is_command_available 'ls'"
}
