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

from collections import Mapping, MutableSequence, Set

from ansible.module_utils.six import string_types, text_type
from ansible.module_utils._text import to_text


__all__ = ['UnsafeProxy', 'AnsibleUnsafe', 'wrap_var']


class AnsibleUnsafe(object):
    __UNSAFE__ = True
    __SOURCE__ = None


class AnsibleUnsafeText(text_type, AnsibleUnsafe):
    pass


# TODO: remove the below Int/Float classes once top-level fact vars have
# been removed. These are only here to allow us to show a deprecation warning
class AnsibleUnsafeInt(int, AnsibleUnsafe):
    pass


class AnsibleUnsafeFloat(float, AnsibleUnsafe):
    pass


class AnsibleUnsafeBool(int, AnsibleUnsafe):

    def __bool__(self):
        if self != 0:
            return True
        return False

    __nonzero__ = __bool__

    def __repr__(self):
        return repr(self.__bool__())

    def __str__(self):
        # XXX: yes, this is terrible. Unfortunately, it seems to be the only way
        # to properly JSON serialize our bool-like object with certain JSON
        # implementations
        caller_frame = sys._getframe().f_back
        # This looks for a caller function name starting with '_iterencode' in
        # a file with 'json' in the name, which should correspond with the JSON
        # encoder
        if caller_frame.f_code.co_name.startswith('_iterencode') and ('json' in caller_frame.f_code.co_filename):
            if self.__bool__():
                return 'true'
            return 'false'
        return str(self.__bool__())


class UnsafeProxy(object):
    def __new__(cls, obj, source=None, *args, **kwargs):
        # In our usage we should only receive unicode strings.
        # This conditional and conversion exists to sanity check the values
        # we're given but we may want to take it out for testing and sanitize
        # our input instead.
        ret = obj
        if isinstance(obj, string_types):
            obj = to_text(obj, errors='surrogate_or_strict')
            ret = AnsibleUnsafeText(obj)
            ret.__SOURCE__ = source
        # TODO: remove the below cases for int/float once top-level fact vars
        # are removed
        # We normally wouldn't consider numeric values as unsafe, but these
        # are here to allow them to be caught for the top-level fact var
        # deprecation warning.
        # We ignore boolean values, because it's not easy to create a bool-like
        # object that works properly in all contexts. This is mostly due to the
        # bool type not being subclassable.
        elif isinstance(obj, bool):
            ret = AnsibleUnsafeBool(obj)
            ret.__SOURCE__ = source
        elif isinstance(obj, int):  # and not isinstance(obj, bool):
            ret = AnsibleUnsafeInt(obj)
            ret.__SOURCE__ = source
        elif isinstance(obj, float):
            ret = AnsibleUnsafeFloat(obj)
            ret.__SOURCE__ = source
        return ret


def _wrap_dict(v, source=None):
    for k in v.keys():
        if v[k] is not None:
            v[wrap_var(k, source)] = wrap_var(v[k], source)
    return v


def _wrap_list(v, source=None):
    for idx, item in enumerate(v):
        if item is not None:
            v[idx] = wrap_var(item, source)
    return v


def wrap_var(v, source=None):
    if isinstance(v, Mapping):
        v = _wrap_dict(v, source)
    elif isinstance(v, (MutableSequence, Set)):
        v = _wrap_list(v, source)
    elif v is not None and not isinstance(v, AnsibleUnsafe):
        v = UnsafeProxy(v, source)
    return v


def check_var_unsafe(val, source=None):
    '''
    Our helper function, which will also recursively check dict and
    list entries due to the fact that they may be repr'd and contain
    a key or value which contains jinja2 syntax and would otherwise
    lose the AnsibleUnsafe value.
    '''
    if isinstance(val, dict):
        for key in val.keys():
            if check_var_unsafe(val[key], source):
                return True
    elif isinstance(val, list):
        for item in val:
            if check_var_unsafe(item, source):
                return True
    elif hasattr(val, '__UNSAFE__'):
        # If no source provided, maintain old behavior where only strings are
        # considered unsafe
        if source is None:
            if isinstance(val, string_types):
                return True
        else:
            if getattr(val, '__SOURCE__', None) == source:
                return True
    return False
