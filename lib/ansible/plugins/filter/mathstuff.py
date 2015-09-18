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

    base = 'bits' if isbits else 'Bytes'
    suffix = ''

    ranges = (
            (1<<70, 'Z'),
            (1<<60, 'E'),
            (1<<50, 'P'),
            (1<<40, 'T'),
            (1<<30, 'G'),
            (1<<20, 'M'),
            (1<<10, 'K'),
            (1, base)
        )

    for limit, suffix in ranges:
        if (unit is None and size >= limit) or \
            unit is not None and unit.upper() == suffix:
            break

    if limit != 1:
        suffix += base[0]

    return '%.2f %s' % (float(size)/ limit, suffix)

def to_bytes(x, si=False):
    ''' convert x to bytes, will parse prefix strings for mb, MB, Mb, etc
        :param: :x - str in the form "2 MB", "2MB", "2GB", etc
        :param: :si - modify multi_factor to use SI values (1000)
    '''


    if (isinstance(x, str) or isinstance(x, unicode) and x):

        if len(x) < 2:
            raise errors.AnsibleFilterError('to_bytes() too short to be a valid format: %s' % x)

        value = ''
        unit = ''
        seen_value = False
        seen_unit = False
        multi_factor = 1000 if si else 1024
        skip_chars = (' ', )

        for char in x.lower():
            if char >= '0' and char <= '9':
                value += char
                seen_value = True
                if seen_unit:
                    raise errors.AnsibleFilterError('to_bytes() invalid format, got more values after unit declared %s' % x)
            elif char >= 'a' and char <= 'z':
                # value is a string, verify we have a number before unit
                if not seen_value:
                    raise errors.AnsibleFilterError('to_bytes() must take a string in the form "64 kB", "128MB", got %s' % x)
                unit += char
                seen_unit = True
            elif char in skip_chars:
                continue
            else:
                raise errors.AnsibleFilterError('to_bytes() unrecognized input: %s' % char)

        value = int(value)

        basebytes = ('b', )
        kilobytes = ('k', 'kb', 'kib', )
        megabytes = ('m', 'mb', 'mib', )
        gigabytes = ('g', 'gb', 'gib', )
        terabytes = ('t', 'tb', 'tib', )
        petabytes = ('p', 'pb', 'pib', )

        if unit in basebytes:
            return value
        elif unit in kilobytes:
            return value * multi_factor
        elif unit in megabytes:
            return value * math.pow(multi_factor, 2)
        elif unit in gigabytes:
            return value * math.pow(multi_factor, 3)
        elif unit in terabytes:
            return value * math.pow(multi_factor, 4)
        elif unit in petabytes:
            return value * math.pow(multi_factor, 5)
        else:
            raise errors.AnsibleFilterError('to_bytes() unrecognized unit: %s' % unit)
    else:
        raise errors.AnsibleFilterError('to_bytes() must take a str or unicode, got %s' % type(x))

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

            # computer theory
            'human_readable' : human_readable,
            'to_bytes': to_bytes,

        }
