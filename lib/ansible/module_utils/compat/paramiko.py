# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import types  # pylint: disable=unused-import
import warnings

PARAMIKO_IMPORT_ERR = None

try:
    with warnings.catch_warnings():
        # Blowfish is deprecated in cryptography, but still used by paramiko versions older than 2.9.5.
        # See: https://github.com/paramiko/paramiko/pull/2039
        warnings.filterwarnings('ignore', message='Blowfish has been ', category=UserWarning)
        # TripleDES is deprecated in cryptography, but still used by current versions of paramiko.
        # See: https://github.com/pyca/cryptography/pull/10286
        # See: https://github.com/ansible/ansible/issues/83757
        warnings.filterwarnings('ignore', message='TripleDES has been ', category=UserWarning)
        import paramiko  # pylint: disable=unused-import
# paramiko and gssapi are incompatible and raise AttributeError not ImportError
# When running in FIPS mode, cryptography raises InternalError
# https://bugzilla.redhat.com/show_bug.cgi?id=1778939
except Exception as err:
    paramiko = None  # type: types.ModuleType | None  # type: ignore[no-redef]
    PARAMIKO_IMPORT_ERR = err
