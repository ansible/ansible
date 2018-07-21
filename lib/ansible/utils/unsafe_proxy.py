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

from collections import Mapping, MutableMapping, MutableSequence, Set

from ansible.module_utils.six import (
    string_types, text_type, iteritems,
    python_2_unicode_compatible)
from ansible.module_utils._text import to_text
from ansible.errors import AnsibleAssertionError


__all__ = ['UnsafeProxy', 'AnsibleUnsafe', 'wrap_var', 'AnsibleDictProxy']


class AnsibleUnsafe(object):
    __UNSAFE__ = True


class AnsibleUnsafeText(text_type, AnsibleUnsafe):
    pass


class UnsafeProxy(object):
    def __new__(cls, obj, *args, **kwargs):
        # In our usage we should only receive unicode strings.
        # This conditional and conversion exists to sanity check the values
        # we're given but we may want to take it out for testing and sanitize
        # our input instead.
        if isinstance(obj, string_types):
            obj = to_text(obj, errors='surrogate_or_strict')
            return AnsibleUnsafeText(obj)
        return obj


class AnsibleObjectProxyMixin(object):
    def _set_resolve(self):
        try:
            self.transform('', resolve=True)
        except TypeError:
            #  Doesn't accept the keyword argument resolve
            def resolve(self):
                raise NotImplementedError()
            self.resolve = resolve.__get__(self)


@python_2_unicode_compatible
class AnsibleDictProxy(MutableMapping, AnsibleObjectProxyMixin):
    """
    Abstract mapping that wraps a dict, transforming keys and values before
    returning them.

    Subclasses must provide a callable attribute `transform`, which will be called on
    values and keys before returning them. `transform` will NOT be called on keys or values
    that are passed in (i.e. we assume `hash(transform(key)) == hash(key)`), nor when
    returning them in the futue.

    `transform` may optionally accept a boolean `resolve`, enabling a method
    `AnsibleDictProxy.resolve` which returns the underlying dict with
    transform applied to it and `resolve=True`, enabling deep resolution of the proxy.
    This is not used currently.

    Exceptions raised in `transform` will propagate.

    Implementations Details:
    - A cache is used to store transformed values (but not keys) on the assumption that value lookups
      are quite common (and that `transform` might be expensive for them). This means that `transform`
      should be idempotent and that you should not depend on it being called for every lookup (only the first).
    - The cache also enables us to Mind Our Own Business, returning values that reside in the cache
      (and so all values set directly by the user) unaltered.
    - `__eq__` compares the underlying dictionaries to avoid `transform`ing as much as possible. i.e. we assume
      `transform(value) == value`
    - `copy` does not preserve the cache, but pickling and unpickling does

    Known Uses:
    - AnsibleUnsafeDict: inherits from AnsibleUnsafe with `transform` set to `wrap_var`
    - template.AnsibleContext.dict_proxy: `transform` marks the Jinja Context as unsafe when an unsafe
                                          key or value is fetched. If the value is a dict, rewrap it.
    """
    # pass isinstance checks
    # inheriting directly from dict has known issues
    __class__ = dict

    def __init__(self, d):
        if not self.transform:
            raise NotImplementedError('Subclasses of AnsibleDictProxy must specify a transform function.')

        if not isinstance(d, type(self)):
            self.wrapped_dict = d
        else:
            self.wrapped_dict = d.wrapped_dict

        self._set_resolve()

        self._cache = {}

    def __getitem__(self, key):
        if key in self._cache:
            return self._cache[key]

        val = self.transform(self.wrapped_dict[key])
        self._cache[key] = val

        return val

    def __setitem__(self, key, val):
        self.wrapped_dict[key] = val
        self._cache[key] = val

    def __delitem__(self, key):
        del self.wrapped_dict[key]
        if key in self._cache:
            del self._cache[key]

    def update(self, other):
        self._cache.update(other)
        self.wrapped_dict.update(other)

    def __contains__(self, key):
        return self.wrapped_dict.__contains__(key)

    def __copy__(self):
        val = type(self)(self.wrapped_dict.copy())
        return val

    def copy(self):
        return self.__copy__()

    # WARNING: Resolve is potentially data-modifying
    def resolve(self):
        if not isinstance(self.wrapped_dict, dict):
            raise AnsibleAssertionError()
        return self.transform(self.wrapped_dict, resolve=True)

    def __iter__(self):
        for k in iter(self.wrapped_dict):
            yield k if k in self._cache else self.transform(k)

    def __len__(self):
        return len(self.wrapped_dict)

    # Avoid MutableMapping's __eq__ as it will copy keys
    def __eq__(self, other):
        if isinstance(other, type(self)):
            other = other.wrapped_dict
        # make the proxy transparent
        if self.wrapped_dict == other:
            return True
        return False

    def __str__(self):
        return u'{{{contents}}}'.format(
            contents=', '.join('{key}: {val}'.format(key=repr(key), val=repr(val))
                               for key, val in iteritems(self)))

    def __repr__(self):
        return self.__str__()

    def __reduce_ex__(self, protocol):
        # for pickling; state is passed to __setstate__
        # -> (constructor, args, state)
        return (type(self), (self.wrapped_dict,), self._cache)

    def __setstate__(self, state):
        self._cache = state


def _wrap_dict(v):
    for k in v:
        if v[k] is not None:
            v[wrap_var(k, resolve=True)] = wrap_var(v[k], resolve=True)
    return v


def _wrap_list(v, resolve=False):
    for idx, item in enumerate(v):
        if item is not None:
            v[idx] = wrap_var(item, resolve=resolve)
    return v


# WARNING: Resolve is data-modifying (though not destructive)
def wrap_var(v, resolve=False):
    if resolve and isinstance(v, AnsibleUnsafeDict):
        v = v.resolve()
    elif isinstance(v, Mapping):
        v = _wrap_dict(v) if resolve else AnsibleUnsafeDict(v)
    elif isinstance(v, (MutableSequence, Set)):
        v = _wrap_list(v, resolve=resolve)
    else:
        if v is not None and not isinstance(v, AnsibleUnsafe):
            v = UnsafeProxy(v)
    return v


class AnsibleUnsafeDict(AnsibleDictProxy, AnsibleUnsafe):
    transform = staticmethod(wrap_var)
