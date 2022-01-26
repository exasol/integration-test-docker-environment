#!/usr/bin/env bash

set -euo pipefail

CHECKSUM_DIRECTORY="$PWD/checksums"
if [ ! -e "$CHECKSUM_DIRECTORY" ]; then
  mkdir "$CHECKSUM_DIRECTORY"
fi
find "$PWD" -maxdepth 1 -type f -printf "%f\\0" | xargs --null -n1 -I{} bash -c "sha512sum {} > '$CHECKSUM_DIRECTORY/{}.sha512sum'"
