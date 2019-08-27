#!/usr/bin/env bash

# Generate key used for CA cert
openssl genrsa -aes256 -out ca.key -passout pass:password 2048

# Generate CA certificate
openssl req -new -x509 -days 365 -key ca.key -out ca.pem -subj "/CN=Ansible Root" -passin pass:password

# Generate key used for signing cert
openssl genrsa -aes256 -out sign.key -passout pass:password 2048

# Generate CSR for signing cert that includes CodeSiging extension
openssl req -new -key sign.key -out sign.csr -subj "/CN=Ansible Sign" -config openssl.conf -reqexts req_sign -passin pass:password

# Generate signing certificate
openssl x509 -req -in sign.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out sign.pem -days 365 -extfile openssl.conf -extensions req_sign -passin pass:password

# Create pfx that includes signing cert and cert with the pass 'password'
openssl pkcs12 -export -out sign.pfx -inkey sign.key -in sign.pem -passin pass:password -passout pass:password
