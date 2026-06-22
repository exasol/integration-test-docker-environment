#!/usr/bin/env bash

set -euo pipefail

DEVICE_SIZE_IN_MEGABYTES=$1

# Setup directory "exa" with pre-configured EXAConf to attach it to the exasoldb docker container
mkdir -p /exa/{etc,data/storage}
cp EXAConf /exa/etc/EXAConf
dd if=/dev/zero of=/exa/data/storage/dev.1 bs=1M count=1 seek="$DEVICE_SIZE_IN_MEGABYTES"
