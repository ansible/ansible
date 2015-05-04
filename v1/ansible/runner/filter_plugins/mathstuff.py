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

from __future__ import absolute_import

import math
import collections
from ansible import errors

def unique(a):
    if isinstance(a,collections.Hashable):
        c = set(a)
    else:
        c = []
        for x in a:
            if x not in c:
                c.append(x)
    return c

def intersect(a, b):
    if isinstance(a,collections.Hashable) and isinstance(b,collections.Hashable):
        c = set(a) & set(b)
    else:
        c = unique(filter(lambda x: x in b, a))
    return c

def difference(a, b):
    if isinstance(a,collections.Hashable) and isinstance(b,collections.Hashable):
        c = set(a) - set(b)
    else:
        c = unique(filter(lambda x: x not in b, a))
    return c

def symmetric_difference(a, b):
    if isinstance(a,collections.Hashable) and isinstance(b,collections.Hashable):
        c = set(a) ^ set(b)
    else:
        c = unique(filter(lambda x: x not in intersect(a,b), union(a,b)))
    return c

def union(a, b):
    if isinstance(a,collections.Hashable) and isinstance(b,collections.Hashable):
        c = set(a) | set(b)
    else:
        c = unique(a + b)
    return c

def min(a):
    _min = __builtins__.get('min')
    return _min(a);

def max(a):
    _max = __builtins__.get('max')
    return _max(a);

def isnotanumber(x):
    try:
        return math.isnan(x)
    except TypeError:
        return False


def logarithm(x, base=math.e):
    try:
        if base == 10:
            return math.log10(x)
        else:
            return math.log(x, base)
    except TypeError, e:
        raise errors.AnsibleFilterError('log() can only be used on numbers: %s' % str(e))


def power(x, y):
    try:
        return math.pow(x, y)
    except TypeError, e:
        raise errors.AnsibleFilterError('pow() can only be used on numbers: %s' % str(e))


def inversepower(x, base=2):
    try:
        if base == 2:
            return math.sqrt(x)
        else:
            return math.pow(x, 1.0/float(base))
    except TypeError, e:
        raise errors.AnsibleFilterError('root() can only be used on numbers: %s' % str(e))


class FilterModule(object):
    ''' Ansible math jinja2 filters '''

    def filters(self):
        return {
            # general math
            'isnan': isnotanumber,
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

        }
