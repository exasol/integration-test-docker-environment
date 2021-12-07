#!/bin/bash

if [[ -d /certificates ]]; then
  find /certificates -type f -name '*.crt' |
    while read P; do cp "$P" /usr/local/share/ca-certificates/; done
fi

update-ca-certificates