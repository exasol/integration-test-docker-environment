#!/bin/bash

set -euo pipefail

NAME={{HOST_NAME}}

echo SubjectName: $NAME

certs_dir={{cert_dir}}

echo Certificate Dir: $certs_dir

if [ ! -d "$certs_dir" ]
then
  mkdir -p "$certs_dir"
fi
pushd "$certs_dir"

# Creae rootCA key and certificate
openssl genrsa -out rootCA.key 2048
openssl req -x509 -nodes -new -key rootCA.key -out rootCA.crt -subj "/C=US/ST=CA/O=Self-signed certificate/CN=$NAME"


# Create server key, certificate request and certificate
echo "[req]
default_bits  = 2048
distinguished_name = req_distinguished_name
req_extensions = req_ext
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
countryName = XX
stateOrProvinceName = N/A
localityName = N/A
organizationName = Self-signed certificate
commonName = $NAME
[req_ext]
subjectAltName = @alt_names
[v3_req]
subjectAltName = @alt_names
[alt_names]
DNS.1 = $NAME
" > san.cnf
openssl genrsa -out cert.key 2048
openssl req -new -sha256 -key cert.key -out cert.csr -config san.cnf
openssl x509 -req -in cert.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out cert.crt -sha256

ls $certs_dir