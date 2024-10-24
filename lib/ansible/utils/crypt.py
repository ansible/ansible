# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import ctypes
import ctypes.util

__all__ = ['CRYPT_NAME', 'crypt']

# prefer ``libcrypt``/``libxcrypt`` over ``libc``
# libc can return None, and still give us the functionality we need
for _lib_name, _allow_none in (('crypt', False), ('c', True)):
    _lib_so = ctypes.util.find_library(_lib_name)
    if not _lib_so and not _allow_none:
        # None will load ``libc`` in LoadLibrary, if we requested ``crypt``
        # we don't want to allow that becoming ``libc``
        continue
    _lib = ctypes.cdll.LoadLibrary(_lib_so)
    try:
        crypt = _lib.crypt
    except AttributeError:
        # Whatever lib this is exists, but is missing ``crypt``
        continue
    crypt.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    crypt.restype = ctypes.c_char_p
    break
else:
    raise ImportError('Cannot find crypt implementation')

CRYPT_NAME = _lib_name
