# Copyright 2014, Brian Coca <bcoca@ansible.com>
# Copyright 2017, Ken Celenza <ken@networktocode.com>
# Copyright 2017, Jason Edelman <jason@networktocode.com>
# Copyright 2017, Ansible Project
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


import collections
import itertools
import math

from ansible import errors
from ansible.module_utils import basic
from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils.six.moves import zip, zip_longest
from ansible.module_utils._text import to_native


def unique(a):
    if isinstance(a, collections.Hashable):
        c = set(a)
    else:
        c = []
        for x in a:
            if x not in c:
                c.append(x)
    return c


def intersect(a, b):
    if isinstance(a, collections.Hashable) and isinstance(b, collections.Hashable):
        c = set(a) & set(b)
    else:
        c = unique([x for x in a if x in b])
    return c


def difference(a, b):
    if isinstance(a, collections.Hashable) and isinstance(b, collections.Hashable):
        c = set(a) - set(b)
    else:
        c = unique([x for x in a if x not in b])
    return c


def symmetric_difference(a, b):
    if isinstance(a, collections.Hashable) and isinstance(b, collections.Hashable):
        c = set(a) ^ set(b)
    else:
        c = unique([x for x in union(a, b) if x not in intersect(a, b)])
    return c


def union(a, b):
    if isinstance(a, collections.Hashable) and isinstance(b, collections.Hashable):
        c = set(a) | set(b)
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
            return math.pow(x, 1.0 / float(base))
    except (ValueError, TypeError) as e:
        raise errors.AnsibleFilterError('root() can only be used on numbers: %s' % str(e))


def human_readable(size, isbits=False, unit=None):
    ''' Return a human readable string '''
    try:
        return basic.bytes_to_human(size, isbits, unit)
    except Exception:
        raise errors.AnsibleFilterError("human_readable() can't interpret following string: %s" % size)


def human_to_bytes(size, default_unit=None, isbits=False):
    ''' Return bytes count from a human readable string '''
    try:
        return basic.human_to_bytes(size, default_unit, isbits)
    except Exception:
        raise errors.AnsibleFilterError("human_to_bytes() can't interpret following string: %s" % size)


def rekey_on_member(data, key, duplicates='error'):
    """
    Rekey a dict of dicts on another member

    May also create a dict from a list of dicts.

    duplicates can be one of ``error`` or ``overwrite`` to specify whether to error out if the key
    value would be duplicated or to overwrite previous entries if that's the case.
    """
    if duplicates not in ('error', 'overwrite'):
        raise errors.AnsibleFilterError("duplicates parameter to rekey_on_member has unknown value: {0}".format(duplicates))

    new_obj = {}

    if isinstance(data, collections.Mapping):
        iterate_over = data.values()
    elif isinstance(data, collections.Iterable) and not isinstance(data, (text_type, binary_type)):
        iterate_over = data
    else:
        raise errors.AnsibleFilterError("Type is not a valid list, set, or dict")

    for item in iterate_over:
        if not isinstance(item, collections.Mapping):
            raise errors.AnsibleFilterError("List item is not a valid dict")

        try:
            key_elem = item[key]
        except KeyError:
            raise errors.AnsibleFilterError("Key {0} was not found".format(key))
        except Exception as e:
            raise errors.AnsibleFilterError(to_native(e))

        # Note: if new_obj[key_elem] exists it will always be a non-empty dict (it will at
        # minimun contain {key: key_elem}
        if new_obj.get(key_elem, None):
            if duplicates == 'error':
                raise errors.AnsibleFilterError("Key {0} is not unique, cannot correctly turn into dict".format(key_elem))
            elif duplicates == 'overwrite':
                new_obj[key_elem] = item
        else:
            new_obj[key_elem] = item

    return new_obj


class FilterModule(object):
    ''' Ansible math jinja2 filters '''

    def filters(self):
        filters = {
            # general math
            'min': min,
            'max': max,

            # exponents and logarithms
            'log': logarithm,
            'pow': power,
            'root': inversepower,

            # set theory
            'unique': unique,
            'intersect': intersect,
            'difference': difference,
            'symmetric_difference': symmetric_difference,
            'union': union,

            # combinatorial
            'product': itertools.product,
            'permutations': itertools.permutations,
            'combinations': itertools.combinations,

            # computer theory
            'human_readable': human_readable,
            'human_to_bytes': human_to_bytes,
            'rekey_on_member': rekey_on_member,

            # zip
            'zip': zip,
            'zip_longest': zip_longest,

        }

        return filters
