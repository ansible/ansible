# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import sys

from ansible.module_utils.common.text.converters import to_native, to_bytes
from ctypes import CDLL, c_char_p, c_int, byref, POINTER, get_errno

try:
    _selinux_lib = CDLL('libselinux.so.1', use_errno=True)
except OSError as ex:
    raise ImportError('unable to load libselinux.so') from ex


def _module_setup():
    def _check_rc(rc):
        if rc < 0:
            errno = get_errno()
            raise OSError(errno, os.strerror(errno))
        return rc

    binary_char_type = type(b'')

    class _to_char_p:
        @classmethod
        def from_param(cls, strvalue):
            if strvalue is not None and not isinstance(strvalue, binary_char_type):
                strvalue = to_bytes(strvalue)

            return strvalue

    # FIXME: swap restype to errcheck

    _funcmap = dict(
        is_selinux_enabled={},
        is_selinux_mls_enabled={},
        lgetfilecon_raw=dict(argtypes=[_to_char_p, POINTER(c_char_p)], restype=_check_rc),
        # NB: matchpathcon is deprecated and should be rewritten on selabel_lookup (but will be a PITA)
        matchpathcon=dict(argtypes=[_to_char_p, c_int, POINTER(c_char_p)], restype=_check_rc),
        security_policyvers={},
        selinux_getenforcemode=dict(argtypes=[POINTER(c_int)]),
        security_getenforce={},
        lsetfilecon=dict(argtypes=[_to_char_p, _to_char_p], restype=_check_rc),
        selinux_getpolicytype=dict(argtypes=[POINTER(c_char_p)], restype=_check_rc),
    )

    _thismod = sys.modules[__name__]

    for fname, cfg in _funcmap.items():
        fn = getattr(_selinux_lib, fname, None)

        if not fn:
            raise ImportError('missing selinux function: {0}'.format(fname))

        # all ctypes pointers share the same base type
        base_ptr_type = type(POINTER(c_int))
        fn.argtypes = cfg.get('argtypes', None)
        fn.restype = cfg.get('restype', c_int)

        # just patch simple directly callable functions directly onto the module
        if not fn.argtypes or not any(argtype for argtype in fn.argtypes if type(argtype) is base_ptr_type):
            setattr(_thismod, fname, fn)
            continue

    # NB: this validation code must run after all the wrappers have been declared
    unimplemented_funcs = set(_funcmap).difference(dir(_thismod))
    if unimplemented_funcs:
        raise NotImplementedError('implementation is missing functions: {0}'.format(unimplemented_funcs))


# begin wrapper function impls

def selinux_getenforcemode():
    enforcemode = c_int()
    rc = _selinux_lib.selinux_getenforcemode(byref(enforcemode))
    return [rc, enforcemode.value]


def selinux_getpolicytype():
    con = c_char_p()
    try:
        rc = _selinux_lib.selinux_getpolicytype(byref(con))
        return [rc, to_native(con.value)]
    finally:
        _selinux_lib.freecon(con)


def lgetfilecon_raw(path):
    con = c_char_p()
    try:
        rc = _selinux_lib.lgetfilecon_raw(path, byref(con))
        return [rc, to_native(con.value)]
    finally:
        _selinux_lib.freecon(con)


def matchpathcon(path, mode):
    con = c_char_p()
    try:
        rc = _selinux_lib.matchpathcon(path, mode, byref(con))
        return [rc, to_native(con.value)]
    finally:
        _selinux_lib.freecon(con)


_module_setup()
del _module_setup

# end wrapper function impls
