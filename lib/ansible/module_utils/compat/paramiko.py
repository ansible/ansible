# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

PARAMIKO_IMPORT_ERR = None

paramiko = None
try:
    import paramiko
# paramiko and gssapi are incompatible and raise AttributeError not ImportError
# When running in FIPS mode, cryptography raises InternalError
# https://bugzilla.redhat.com/show_bug.cgi?id=1778939
except Exception as err:
    PARAMIKO_IMPORT_ERR = err
