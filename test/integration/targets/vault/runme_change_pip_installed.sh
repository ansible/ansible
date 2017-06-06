#!/bin/bash

# start by removing pycrypto and cryptography

pip uninstall -y cryptography
pip uninstall -y pycrypto

# this will fail in some fashion or another, but
# need to decide what is expected and test for it
./runme.sh "$@"

# now just pycrypto
pip install --user pycrypto

# start enforcing success
set -e
./runme.sh "$@"


# now just cryptography

pip uninstall -y pycrypto
pip install --user cryptography

./runme.sh "$@"

# now both

pip install --user pycrypto

./runme.sh "$@"
