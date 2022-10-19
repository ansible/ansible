# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import types
import warnings

PARAMIKO_IMPORT_ERR = None

try:
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Blowfish has been deprecated', category=UserWarning)
        import paramiko
# paramiko and gssapi are incompatible and raise AttributeError not ImportError
# When running in FIPS mode, cryptography raises InternalError
# https://bugzilla.redhat.com/show_bug.cgi?id=1778939
except Exception as err:
    paramiko = None  # type: types.ModuleType | None  # type: ignore[no-redef]
    PARAMIKO_IMPORT_ERR = err
