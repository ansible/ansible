# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation
# ("PSF"), and the Individual or Organization ("Licensee") accessing and
# otherwise using this software ("Python") in source or binary form and
# its associated documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby
# grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
# analyze, test, perform and/or display publicly, prepare derivative works,
# distribute, and otherwise use Python alone or in any derivative version,
# provided, however, that PSF's License Agreement and PSF's notice of copyright,
# i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
# 2011, 2012, 2013, 2014 Python Software Foundation; All Rights Reserved" are
# retained in Python alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on
# or incorporates Python or any part thereof, and wants to make
# the derivative work available to others as provided herein, then
# Licensee hereby agrees to include in any such work a brief summary of
# the changes made to Python.
#
# 4. PSF is making Python available to Licensee on an "AS IS"
# basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
# IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
# DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
# FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
# INFRINGE ANY THIRD PARTY RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
# FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
# A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
# OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material
# breach of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any
# relationship of agency, partnership, or joint venture between PSF and
# Licensee.  This License Agreement does not grant permission to use PSF
# trademarks or trade name in a trademark sense to endorse or promote
# products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python, Licensee
# agrees to be bound by the terms and conditions of this License
# Agreement.
#
# Original Python Recipe for Proxy:
# http://code.activestate.com/recipes/496741-object-proxying/
# Author: Tomer Filiba

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import types
import warnings
from sys import intern as _sys_intern
from collections.abc import Mapping, Set

from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common.collections import is_sequence
from ansible.utils.native_jinja import NativeJinjaText


__all__ = ['AnsibleUnsafe', 'wrap_var']


class AnsibleUnsafe(object):
    __UNSAFE__ = True


class AnsibleUnsafeBytes(bytes, AnsibleUnsafe):
    def _strip_unsafe(self):
        return super().__bytes__()

    def __reduce__(self, /):
        return (self.__class__, (self._strip_unsafe(),))

    def __str__(self, /):  # pylint: disable=invalid-str-returned
        return self.decode()

    def __bytes__(self, /):  # pylint: disable=invalid-bytes-returned
        return self

    def __repr__(self, /):  # pylint: disable=invalid-repr-returned
        return AnsibleUnsafeText(super().__repr__())

    def __format__(self, format_spec, /):  # pylint: disable=invalid-format-returned
        return AnsibleUnsafeText(super().__format__(format_spec))

    def __getitem__(self, key, /):
        if isinstance(key, int):
            return super().__getitem__(key)
        return self.__class__(super().__getitem__(key))

    def __reversed__(self, /):
        return self[::-1]

    def __add__(self, value, /):
        return self.__class__(super().__add__(value))

    def __radd__(self, value, /):
        return self.__class__(value.__add__(self))

    def __mul__(self, value, /):
        return self.__class__(super().__mul__(value))

    __rmul__ = __mul__

    def __mod__(self, value, /):
        return self.__class__(super().__mod__(value))

    def __rmod__(self, value, /):
        return self.__class__(super().__rmod__(value))

    def capitalize(self, /):
        return self.__class__(super().capitalize())

    def center(self, width, fillchar=b' ', /):
        return self.__class__(super().center(width, fillchar))

    def decode(self, /, encoding='utf-8', errors='strict'):
        return AnsibleUnsafeText(super().decode(encoding=encoding, errors=errors))

    def removeprefix(self, prefix, /):
        return self.__class__(super().removeprefix(prefix))

    def removesuffix(self, suffix, /):
        return self.__class__(super().removesuffix(suffix))

    def expandtabs(self, /, tabsize=8):
        return self.__class__(super().expandtabs(tabsize))

    def join(self, iterable_of_bytes, /):
        return self.__class__(super().join(iterable_of_bytes))

    def ljust(self, width, fillchar=b' ', /):
        return self.__class__(super().ljust(width, fillchar))

    def lower(self, /):
        return self.__class__(super().lower())

    def lstrip(self, chars=None, /):
        return self.__class__(super().lstrip(chars))

    def partition(self, sep, /):
        cls = self.__class__
        return tuple(cls(e) for e in super().partition(sep))

    def replace(self, old, new, count=-1, /):
        return self.__class__(super().replace(old, new, count))

    def rjust(self, width, fillchar=b' ', /):
        return self.__class__(super().rjust(width, fillchar))

    def rpartition(self, sep, /):
        cls = self.__class__
        return tuple(cls(e) for e in super().rpartition(sep))

    def rstrip(self, chars=None, /):
        return self.__class__(super().rstrip(chars))

    def split(self, /, sep=None, maxsplit=-1):
        cls = self.__class__
        return [cls(e) for e in super().split(sep=sep, maxsplit=maxsplit)]

    def rsplit(self, /, sep=None, maxsplit=-1):
        cls = self.__class__
        return [cls(e) for e in super().rsplit(sep=sep, maxsplit=maxsplit)]

    def splitlines(self, /, keepends=False):
        cls = self.__class__
        return [cls(e) for e in super().splitlines(keepends=keepends)]

    def strip(self, chars=None, /):
        return self.__class__(super().strip(chars))

    def swapcase(self, /):
        return self.__class__(super().swapcase())

    def title(self, /):
        return self.__class__(super().title())

    def translate(self, table, /, delete=b''):
        return self.__class__(super().translate(table, delete=delete))

    def upper(self, /):
        return self.__class__(super().upper())

    def zfill(self, width, /):
        return self.__class__(super().zfill(width))


class AnsibleUnsafeText(str, AnsibleUnsafe):
    def _strip_unsafe(self, /):
        return super().__str__()

    def __reduce__(self, /):
        return (self.__class__, (self._strip_unsafe(),))

    def __str__(self, /):  # pylint: disable=invalid-str-returned
        return self

    def __repr__(self, /):  # pylint: disable=invalid-repr-returned
        return self.__class__(super().__repr__())

    def __format__(self, format_spec, /):  # pylint: disable=invalid-format-returned
        return self.__class__(super().__format__(format_spec))

    def __getitem__(self, key, /):
        return self.__class__(super().__getitem__(key))

    def __iter__(self, /):
        cls = self.__class__
        return (cls(c) for c in super().__iter__())

    def __reversed__(self, /):
        return self[::-1]

    def __add__(self, value, /):
        return self.__class__(super().__add__(value))

    def __radd__(self, value, /):
        return self.__class__(value.__add__(self))

    def __mul__(self, value, /):
        return self.__class__(super().__mul__(value))

    __rmul__ = __mul__

    def __mod__(self, value, /):
        return self.__class__(super().__mod__(value))

    def __rmod__(self, value, /):
        return self.__class__(super().__rmod__(value))

    def capitalize(self, /):
        return self.__class__(super().capitalize())

    def casefold(self, /):
        return self.__class__(super().casefold())

    def center(self, width, fillchar=' ', /):
        return self.__class__(super().center(width, fillchar))

    def encode(self, /, encoding='utf-8', errors='strict'):
        return AnsibleUnsafeBytes(super().encode(encoding=encoding, errors=errors))

    def removeprefix(self, prefix, /):
        return self.__class__(super().removeprefix(prefix))

    def removesuffix(self, suffix, /):
        return self.__class__(super().removesuffix(suffix))

    def expandtabs(self, /, tabsize=8):
        return self.__class__(super().expandtabs(tabsize))

    def format(self, /, *args, **kwargs):
        return self.__class__(super().format(*args, **kwargs))

    def format_map(self, mapping, /):
        return self.__class__(super().format_map(mapping))

    def join(self, iterable, /):
        return self.__class__(super().join(iterable))

    def ljust(self, width, fillchar=' ', /):
        return self.__class__(super().ljust(width, fillchar))

    def lower(self, /):
        return self.__class__(super().lower())

    def lstrip(self, chars=None, /):
        return self.__class__(super().lstrip(chars))

    def partition(self, sep, /):
        cls = self.__class__
        return tuple(cls(e) for e in super().partition(sep))

    def replace(self, old, new, count=-1, /):
        return self.__class__(super().replace(old, new, count))

    def rjust(self, width, fillchar=' ', /):
        return self.__class__(super().rjust(width, fillchar))

    def rpartition(self, sep, /):
        cls = self.__class__
        return tuple(cls(e) for e in super().rpartition(sep))

    def rstrip(self, chars=None, /):
        return self.__class__(super().rstrip(chars))

    def split(self, /, sep=None, maxsplit=-1):
        cls = self.__class__
        return [cls(e) for e in super().split(sep=sep, maxsplit=maxsplit)]

    def rsplit(self, /, sep=None, maxsplit=-1):
        cls = self.__class__
        return [cls(e) for e in super().rsplit(sep=sep, maxsplit=maxsplit)]

    def splitlines(self, /, keepends=False):
        cls = self.__class__
        return [cls(e) for e in super().splitlines(keepends=keepends)]

    def strip(self, chars=None, /):
        return self.__class__(super().strip(chars))

    def swapcase(self, /):
        return self.__class__(super().swapcase())

    def title(self, /):
        return self.__class__(super().title())

    def translate(self, table, /):
        return self.__class__(super().translate(table))

    def upper(self, /):
        return self.__class__(super().upper())

    def zfill(self, width, /):
        return self.__class__(super().zfill(width))


class NativeJinjaUnsafeText(NativeJinjaText, AnsibleUnsafeText):
    pass


def _wrap_dict(v):
    return dict((wrap_var(k), wrap_var(item)) for k, item in v.items())


def _wrap_sequence(v):
    """Wraps a sequence with unsafe, not meant for strings, primarily
    ``tuple`` and ``list``
    """
    v_type = type(v)
    return v_type(wrap_var(item) for item in v)


def _wrap_set(v):
    return set(wrap_var(item) for item in v)


def wrap_var(v):
    if v is None or isinstance(v, AnsibleUnsafe):
        return v

    if isinstance(v, Mapping):
        v = _wrap_dict(v)
    elif isinstance(v, Set):
        v = _wrap_set(v)
    elif is_sequence(v):
        v = _wrap_sequence(v)
    elif isinstance(v, NativeJinjaText):
        v = NativeJinjaUnsafeText(v)
    elif isinstance(v, bytes):
        v = AnsibleUnsafeBytes(v)
    elif isinstance(v, str):
        v = AnsibleUnsafeText(v)

    return v


def to_unsafe_bytes(*args, **kwargs):
    return wrap_var(to_bytes(*args, **kwargs))


def to_unsafe_text(*args, **kwargs):
    return wrap_var(to_text(*args, **kwargs))


def _is_unsafe(obj):
    return getattr(obj, '__UNSAFE__', False) is True


def _intern(string):
    """This is a monkey patch for ``sys.intern`` that will strip
    the unsafe wrapper prior to interning the string.

    This will not exist in future versions.
    """
    if isinstance(string, AnsibleUnsafeText):
        string = string._strip_unsafe()
    return _sys_intern(string)


if isinstance(sys.intern, types.BuiltinFunctionType):
    sys.intern = _intern
else:
    warnings.warn("skipped sys.intern patch; appears to have already been patched", RuntimeWarning)
