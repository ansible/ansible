# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

PARAMIKO_IMPORT_ERR = None

paramiko = None
try:
    # if paramiko *is* installed, it attempts to generate an x25519 key at
    # import time; this isn't supported on platforms where FIPS is enabled
    # this code exists to properly detect FIPS-enablement on certain RHEL
    # platforms so that ansible-playbook can run
    #
    # related: https://github.com/pyca/cryptography/pull/5024
    from cryptography.hazmat.backends.openssl.backend import Backend
    def _x25519_supported(self):
        fips_mode = getattr(self._lib, "FIPS_mode", lambda: 0)
        mode = fips_mode()
        if mode:
            return False
        if mode == 0:
            # OpenSSL without FIPS pushes an error on the error stack
            self._lib.ERR_clear_error()
        return self._lib.CRYPTOGRAPHY_OPENSSL_110_OR_GREATER
    Backend.x25519_supported = _x25519_supported

    import paramiko
except (ImportError, AttributeError) as err:  # paramiko and gssapi are incompatible and raise AttributeError not ImportError
    PARAMIKO_IMPORT_ERR = err
