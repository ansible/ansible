#!/usr/bin/env bash

set -eux

# First install pyOpenSSL, then test lookup in a second playbook in order to
# workaround this error which occurs on OS X 10.11 only:
#
# TASK [lookup_hashi_vault : test token auth with certs (validation enabled, lookup parameters)] ***
# included: lookup_hashi_vault/tasks/token_test.yml for testhost
#
#   TASK [lookup_hashi_vault : Fetch secrets using "hashi_vault" lookup] ***
#   From cffi callback <function _verify_callback at 0x106f995f0>:
#   Traceback (most recent call last):
#     File "/usr/local/lib/python2.7/site-packages/OpenSSL/SSL.py", line 309, in wrapper
#       _lib.X509_up_ref(x509)
#   AttributeError: 'module' object has no attribute 'X509_up_ref'
#   fatal: [testhost]: FAILED! => { "msg": "An unhandled exception occurred while running the lookup plugin 'hashi_vault'. Error was a <class 'requests.exceptions.SSLError'>, original message: HTTPSConnectionPool(host='localhost', port=8201): Max retries exceeded with url: /v1/auth/token/lookup-self (Caused by SSLError(SSLError(\"bad handshake: Error([('SSL routines', 'ssl3_get_server_certificate', 'certificate verify failed')],)\",),))"}

ANSIBLE_ROLES_PATH=../ \
    ansible-playbook playbooks/install_dependencies.yml -v "$@"

ANSIBLE_ROLES_PATH=../ \
    ansible-playbook playbooks/test_lookup_hashi_vault.yml -v "$@"
