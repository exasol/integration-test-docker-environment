#!/bin/bash


#######################################################################################
# This script is intended to run on a test-container to install the new certificates. #
#######################################################################################

set -euo pipefail

#Install Linux certificates (useful for pyexasol)
cp /certificates/rootCA.crt /usr/local/share/ca-certificates/
update-ca-certificates

#Update java ca certs
keytool -keystore /etc/ssl/certs/java/cacerts -import -file /certificates/rootCA.crt -storepass changeit -noprompt