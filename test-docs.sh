#!/bin/sh
set -x

CHECKOUT_DIR=".ansible-checkout"
MOD_REPO="$1"

# Hidden file to avoid the module_formatter recursing into the checkout
git clone https://github.com/ansible/ansible "$CHECKOUT_DIR"
cd "$CHECKOUT_DIR"
git submodule update --init
rm -rf "lib/ansible/modules/$MOD_REPO"
ln -s "$TRAVIS_BUILD_DIR/" "lib/ansible/modules/$MOD_REPO"

pip install -U Jinja2 PyYAML setuptools six pycrypto sphinx

. ./hacking/env-setup
PAGER=/bin/cat bin/ansible-doc -l
if [ $? -ne 0 ] ; then
  exit $?
fi
make -C docsite
