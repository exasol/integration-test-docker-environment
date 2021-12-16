#!/bin/bash

set -euo pipefail

#Install Linux certificates (useful for pyexasol)
cp /certificates/rootCA.crt /usr/local/share/ca-certificates/
update-ca-certificates

#Update java ca certs
keytool -keystore /etc/ssl/certs/java/cacerts -import -file /certificates/rootCA.crt -storepass changeit -noprompt