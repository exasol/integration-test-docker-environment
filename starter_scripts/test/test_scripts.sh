#!/usr/bin/env bash

#set -e => immediately exit if any command [1] has a non-zero exit status
#set -u => reference to any variable you haven't previously defined is an error and causes the program to immediately exit.
#set -o pipefailt => This setting prevents errors in a pipeline from being masked.
#                    If any command in a pipeline fails,
#                    that return code will be used as the return code of the whole pipeline.
set -euo pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"/..

function assert() {
  cmpA=$1
  shift 1
  cmpB="${*}"
  if [[ $cmpA != "$cmpB" ]]; then
    >&2 echo "ERROR: '$cmpA' does not match'$cmpB'"
    exit 1
  fi
}

cacheDirectory="$SCRIPT_DIR/test/abc=def"
saveDirectory="$SCRIPT_DIR/test/exportdir=xyz"

mkdir "$cacheDirectory" || true
trap 'rm -rf "$cacheDirectory" "$saveDirectory"' EXIT

testStr=$(bash "$SCRIPT_DIR/mount_point_parsing.sh" --cache-directory="$cacheDirectory" --save-directory "$saveDirectory" dummy)

assert "$testStr" "$cacheDirectory" "$saveDirectory"
