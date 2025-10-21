# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
from dataclasses import dataclass

__all__ = ['CRYPT_NAME', 'crypt', 'crypt_gensalt', 'HAS_CRYPT_GENSALT']

_FAILURE_TOKENS = frozenset({b'*0', b'*1'})


@dataclass(frozen=True)
class _CryptLib:
    name: str | None
    exclude_platforms: frozenset[str] = frozenset()
    include_platforms: frozenset[str] = frozenset()
    is_path: bool = False


_CRYPT_LIBS = (
    _CryptLib('crypt'),  # libxcrypt
    _CryptLib(None, exclude_platforms=frozenset({'darwin'})),  # fallback to default libc
    _CryptLib(  # macOS Homebrew (Apple Silicon)
        '/opt/homebrew/opt/libxcrypt/lib/libcrypt.dylib',
        include_platforms=frozenset({'darwin'}),
        is_path=True,
    ),
    _CryptLib(  # macOS Homebrew (Intel)
        '/usr/local/opt/libxcrypt/lib/libcrypt.dylib',
        include_platforms=frozenset({'darwin'}),
        is_path=True,
    ),
)

for _lib_config in _CRYPT_LIBS:
    if sys.platform in _lib_config.exclude_platforms:
        continue
    if _lib_config.include_platforms and sys.platform not in _lib_config.include_platforms:
        continue

    if _lib_config.name is None:
        _lib_so = None
    elif _lib_config.is_path:
        if os.path.exists(_lib_config.name):
            _lib_so = _lib_config.name
        else:
            continue
    else:
        _lib_so = ctypes.util.find_library(_lib_config.name)
        if not _lib_so:
            continue

    _lib = ctypes.cdll.LoadLibrary(_lib_so)

    _use_crypt_r = False
    try:
        _crypt_impl = _lib.crypt_r
        _use_crypt_r = True
    except AttributeError:
        try:
            _crypt_impl = _lib.crypt
        except AttributeError:
            continue

    if _use_crypt_r:

        class _crypt_data(ctypes.Structure):
            _fields_ = [('_opaque', ctypes.c_char * 131072)]

        _crypt_impl.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(_crypt_data)]
        _crypt_impl.restype = ctypes.c_char_p
    else:
        _crypt_impl.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        _crypt_impl.restype = ctypes.c_char_p

    # Try to load crypt_gensalt (available in libxcrypt)
    _use_crypt_gensalt_rn = False
    HAS_CRYPT_GENSALT = False
    try:
        _crypt_gensalt_impl = _lib.crypt_gensalt_rn
        _crypt_gensalt_impl.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
        _crypt_gensalt_impl.restype = ctypes.c_char_p
        _use_crypt_gensalt_rn = True
        HAS_CRYPT_GENSALT = True
    except AttributeError:
        try:
            _crypt_gensalt_impl = _lib.crypt_gensalt
            _crypt_gensalt_impl.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int]
            _crypt_gensalt_impl.restype = ctypes.c_char_p
            HAS_CRYPT_GENSALT = True
        except AttributeError:
            _crypt_gensalt_impl = None

    CRYPT_NAME = _lib_config.name
    break
else:
    raise ImportError('Cannot find crypt implementation')


def crypt(word: bytes, salt: bytes) -> bytes:
    """Hash a password using the system's crypt function."""
    ctypes.set_errno(0)

    if _use_crypt_r:
        data = _crypt_data()
        ctypes.memset(ctypes.byref(data), 0, ctypes.sizeof(data))
        result = _crypt_impl(word, salt, ctypes.byref(data))
    else:
        result = _crypt_impl(word, salt)

    errno = ctypes.get_errno()
    if errno:
        error_msg = os.strerror(errno)
        raise OSError(errno, f'crypt failed: {error_msg}')

    if result is None:
        raise ValueError('crypt failed: invalid salt or unsupported algorithm')

    if result in _FAILURE_TOKENS:
        raise ValueError('crypt failed: invalid salt or unsupported algorithm')

    return result


def crypt_gensalt(prefix: bytes, count: int, rbytes: bytes) -> bytes:
    """Generate a salt string for use with crypt."""
    if not HAS_CRYPT_GENSALT:
        raise NotImplementedError('crypt_gensalt not available (requires libxcrypt)')

    ctypes.set_errno(0)

    if _use_crypt_gensalt_rn:
        output = ctypes.create_string_buffer(256)
        result = _crypt_gensalt_impl(prefix, count, rbytes, len(rbytes), output, len(output))
        if result is not None:
            result = output.value
    else:
        result = _crypt_gensalt_impl(prefix, count, rbytes, len(rbytes))

    errno = ctypes.get_errno()
    if errno:
        error_msg = os.strerror(errno)
        raise OSError(errno, f'crypt_gensalt failed: {error_msg}')

    if result is None:
        raise ValueError('crypt_gensalt failed: unable to generate salt')

    if result in _FAILURE_TOKENS:
        raise ValueError('crypt_gensalt failed: invalid prefix or unsupported algorithm')

    return result


del _lib_config
