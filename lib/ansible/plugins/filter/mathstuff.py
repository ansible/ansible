# (c) 2014, Brian Coca <bcoca@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import math
from collections import Hashable, Mapping
from ansible import errors
from ansible.module_utils import basic

def unique(a):
    if isinstance(a, Hashable):
        c = set(a)
    elif isinstance(a, Mapping):
        c = a
    else:
        c = []
        for x in a:
            if x not in c:
                c.append(x)
    return c

def intersect(a, b, strict=False):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) & set(b)
    elif isinstance(a, Mapping) and isinstance(b, Mapping):
        c = {}
        for k in intersect(a.keys(),b.keys()):
            if strict:
                if a[k] == b[k]:
                    c[k] = a[k]
            else:
                c[k] = a[k]
    else:
        c = unique(filter(lambda x: x in b, a))
    return c

def difference(a, b, strict=False):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) - set(b)
    elif isinstance(a, Mapping) and isinstance(b, Mapping):
        c = {}
        # get keys that are different
        for k in difference(a.keys(),b.keys()):
            c[k] = a[k]

        if strict:
            # get values that are different
            for k in intersect(a.keys(), b.keys()):
                if a[k] != b[k]:
                    c[k] = a[k]
    else:
        c = unique(filter(lambda x: x not in b, a))
    return c

def symmetric_difference(a, b, strict=False):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) ^ set(b)
    elif isinstance(a, Mapping) and isinstance(b, Mapping):
        c={}
        # get keys that are different
        for k in symmetric_difference(a.keys(),b.keys()):
            if k in b:
                c[k] = b[k]
            else:
                c[k] = a[k]

        if strict:
            # get values that are different
            for k in intersect(a.keys(), b.keys()):
                if a[k] != b[k]:
                    c[k] = a[k]
    else:
        c = unique(filter(lambda x: x not in intersect(a,b), union(a,b)))
    return c

def union(a, b):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) | set(b)
    elif isinstance(a, Mapping) and isinstance(b, Mapping):
        c = b.copy()
        c.update(a)
    else:
        c = unique(a + b)
    return c

def min(a):
    _min = __builtins__.get('min')
    return _min(a)

def max(a):
    _max = __builtins__.get('max')
    return _max(a)


def logarithm(x, base=math.e):
    try:
        if base == 10:
            return math.log10(x)
        else:
            return math.log(x, base)
    except TypeError as e:
        raise errors.AnsibleFilterError('log() can only be used on numbers: %s' % str(e))


def power(x, y):
    try:
        return math.pow(x, y)
    except TypeError as e:
        raise errors.AnsibleFilterError('pow() can only be used on numbers: %s' % str(e))


def inversepower(x, base=2):
    try:
        if base == 2:
            return math.sqrt(x)
        else:
            return math.pow(x, 1.0/float(base))
    except TypeError as e:
        raise errors.AnsibleFilterError('root() can only be used on numbers: %s' % str(e))


def human_readable(size, isbits=False, unit=None):
    ''' Return a human readable string '''
    try:
        return basic.bytes_to_human(size, isbits, unit)
    except:
        raise errors.AnsibleFilterError("human_readable() can't interpret following string: %s" % size)

def human_to_bytes(size, default_unit=None, isbits=False):
    ''' Return bytes count from a human readable string '''
    try:
        return basic.human_to_bytes(size, default_unit, isbits)
    except:
        raise errors.AnsibleFilterError("human_to_bytes() can't interpret following string: %s" % size)

class FilterModule(object):
    ''' Ansible math jinja2 filters '''

    def filters(self):
        return {
            # general math
            'min' : min,
            'max' : max,

            # exponents and logarithms
            'log': logarithm,
            'pow': power,
            'root': inversepower,

            # set theory
            'unique' : unique,
            'intersect': intersect,
            'difference': difference,
            'symmetric_difference': symmetric_difference,
            'union': union,

            # computer theory
            'human_readable' : human_readable,
            'human_to_bytes' : human_to_bytes,

        }
