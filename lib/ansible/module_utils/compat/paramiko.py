# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations as _annotations

import warnings as _warnings

from ansible.module_utils.common.warnings import deprecate as _deprecate

_PARAMIKO_IMPORT_ERR = None

try:
    with _warnings.catch_warnings():
        # Blowfish has been moved, but the deprecated import is used by paramiko versions older than 2.9.5.
        # See: https://github.com/paramiko/paramiko/pull/2039
        _warnings.filterwarnings('ignore', message='Blowfish has been ', category=UserWarning)
        # TripleDES has been moved, but the deprecated import is used by paramiko versions older than 3.3.2 and 3.4.1.
        # See: https://github.com/paramiko/paramiko/pull/2421
        _warnings.filterwarnings('ignore', message='TripleDES has been ', category=UserWarning)
        import paramiko as _paramiko
# paramiko and gssapi are incompatible and raise AttributeError not ImportError
# When running in FIPS mode, cryptography raises InternalError
# https://bugzilla.redhat.com/show_bug.cgi?id=1778939
except Exception as err:
    _paramiko = None  # type: ignore[no-redef]
    _PARAMIKO_IMPORT_ERR = err


def __getattr__(name: str) -> object:
    """Dynamic lookup to issue deprecation warnings for external import of deprecated items."""
    if (res := globals().get(f'_{name}', ...)) is not ...:
        _deprecate(f'The {name!r} compat import is deprecated.', version='2.21')

        return res

    raise AttributeError(name)
