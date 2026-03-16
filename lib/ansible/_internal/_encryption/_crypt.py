# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import ctypes
import ctypes.util
import os
import sys
import typing as t
from dataclasses import dataclass

__all__ = ['CryptFacade']

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


class CryptFacade:
    """
    Provide an interface for various crypt libraries that might be available.
    """

    def __init__(self) -> None:
        self._crypt_impl: t.Callable | None = None
        self._crypt_gensalt_impl: t.Callable | None = None
        self._use_crypt_r = False
        self._use_crypt_gensalt_rn = False
        self._crypt_name = ""

        self._setup()

    class _CryptData(ctypes.Structure):
        _fields_ = [('_opaque', ctypes.c_char * 131072)]

    @property
    def has_crypt_gensalt(self) -> bool:
        return self._crypt_gensalt_impl is not None

    def _setup(self) -> None:
        """Setup crypt implementation"""
        for lib_config in _CRYPT_LIBS:
            if sys.platform in lib_config.exclude_platforms:
                continue
            if lib_config.include_platforms and sys.platform not in lib_config.include_platforms:
                continue

            if lib_config.name is None:
                lib_so = None
            elif lib_config.is_path:
                if os.path.exists(lib_config.name):
                    lib_so = lib_config.name
                else:
                    continue
            else:
                lib_so = ctypes.util.find_library(lib_config.name)
                if not lib_so:
                    continue

            loaded_lib = ctypes.cdll.LoadLibrary(lib_so)

            try:
                self._crypt_impl = loaded_lib.crypt_r
                self._use_crypt_r = True
            except AttributeError:
                try:
                    self._crypt_impl = loaded_lib.crypt
                except AttributeError:
                    continue

            if self._use_crypt_r:
                self._crypt_impl.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(self._CryptData)]
                self._crypt_impl.restype = ctypes.c_char_p
            else:
                self._crypt_impl.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
                self._crypt_impl.restype = ctypes.c_char_p

            # Try to load crypt_gensalt (available in libxcrypt)
            try:
                self._crypt_gensalt_impl = loaded_lib.crypt_gensalt_rn
                self._crypt_gensalt_impl.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
                self._crypt_gensalt_impl.restype = ctypes.c_char_p
                self._use_crypt_gensalt_rn = True
            except AttributeError:
                try:
                    self._crypt_gensalt_impl = loaded_lib.crypt_gensalt
                    self._crypt_gensalt_impl.argtypes = [ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_int]
                    self._crypt_gensalt_impl.restype = ctypes.c_char_p
                except AttributeError:
                    self._crypt_gensalt_impl = None

            self._crypt_name = lib_config.name
            break
        else:
            raise ImportError('Cannot find crypt implementation')

    def crypt(self, word: bytes, salt: bytes) -> bytes:
        """Hash a password using the system's crypt function."""
        ctypes.set_errno(0)

        if self._use_crypt_r:
            data = self._CryptData()
            ctypes.memset(ctypes.byref(data), 0, ctypes.sizeof(data))
            result = self._crypt_impl(word, salt, ctypes.byref(data))
        else:
            result = self._crypt_impl(word, salt)

        errno = ctypes.get_errno()
        if errno:
            error_msg = os.strerror(errno)
            raise OSError(errno, f'crypt failed: {error_msg}')

        if result is None:
            raise ValueError('crypt failed: invalid salt or unsupported algorithm')

        if result in _FAILURE_TOKENS:
            raise ValueError('crypt failed: invalid salt or unsupported algorithm')

        return result

    def crypt_gensalt(self, prefix: bytes, count: int, rbytes: bytes) -> bytes:
        """Generate a salt string for use with crypt."""
        if not self.has_crypt_gensalt:
            raise NotImplementedError('crypt_gensalt not available (requires libxcrypt)')

        ctypes.set_errno(0)

        if self._use_crypt_gensalt_rn:
            output = ctypes.create_string_buffer(256)
            result = self._crypt_gensalt_impl(prefix, count, rbytes, len(rbytes), output, len(output))
            if result is not None:
                result = output.value
        else:
            result = self._crypt_gensalt_impl(prefix, count, rbytes, len(rbytes))

        errno = ctypes.get_errno()
        if errno:
            error_msg = os.strerror(errno)
            raise OSError(errno, f'crypt_gensalt failed: {error_msg}')

        if result is None:
            raise ValueError('crypt_gensalt failed: unable to generate salt')

        if result in _FAILURE_TOKENS:
            raise ValueError('crypt_gensalt failed: invalid prefix or unsupported algorithm')

        return result
