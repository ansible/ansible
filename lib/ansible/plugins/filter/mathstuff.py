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

import itertools
import math

from collections.abc import Hashable, Mapping, Iterable

from jinja2.filters import pass_environment

from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError
from ansible.module_utils.common.text import formatters
from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils._text import to_native, to_text
from ansible.utils.display import Display

try:
    from jinja2.filters import do_unique
    HAS_UNIQUE = True
except ImportError:
    HAS_UNIQUE = False


display = Display()


@pass_environment
# Use case_sensitive=None as a sentinel value, so we raise an error only when
# explicitly set and cannot be handle (by Jinja2 w/o 'unique' or fallback version)
def unique(environment, a, case_sensitive=None, attribute=None):

    def _do_fail(e):
        if case_sensitive is False or attribute:
            raise AnsibleFilterError("Jinja2's unique filter failed and we cannot fall back to Ansible's version "
                                     "as it does not support the parameters supplied", orig_exc=e)

    error = e = None
    try:
        if HAS_UNIQUE:
            c = list(do_unique(environment, a, case_sensitive=bool(case_sensitive), attribute=attribute))
    except TypeError as e:
        error = e
        _do_fail(e)
    except Exception as e:
        error = e
        _do_fail(e)
        display.warning('Falling back to Ansible unique filter as Jinja2 one failed: %s' % to_text(e))

    if not HAS_UNIQUE or error:

        # handle Jinja2 specific attributes when using Ansible's version
        if case_sensitive is False or attribute:
            raise AnsibleFilterError("Ansible's unique filter does not support case_sensitive=False nor attribute parameters, "
                                     "you need a newer version of Jinja2 that provides their version of the filter.")

        c = []
        for x in a:
            if x not in c:
                c.append(x)

    return c


@pass_environment
def intersect(environment, a, b):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) & set(b)
    else:
        c = unique(environment, [x for x in a if x in b], True)
    return c


@pass_environment
def difference(environment, a, b):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) - set(b)
    else:
        c = unique(environment, [x for x in a if x not in b], True)
    return c


@pass_environment
def symmetric_difference(environment, a, b):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) ^ set(b)
    else:
        isect = intersect(environment, a, b)
        c = [x for x in union(environment, a, b) if x not in isect]
    return c


@pass_environment
def union(environment, a, b):
    if isinstance(a, Hashable) and isinstance(b, Hashable):
        c = set(a) | set(b)
    else:
        c = unique(environment, a + b, True)
    return c


def logarithm(x, base=math.e):
    try:
        if base == 10:
            return math.log10(x)
        else:
            return math.log(x, base)
    except TypeError as e:
        raise AnsibleFilterTypeError('log() can only be used on numbers: %s' % to_native(e))


def power(x, y):
    try:
        return math.pow(x, y)
    except TypeError as e:
        raise AnsibleFilterTypeError('pow() can only be used on numbers: %s' % to_native(e))


def inversepower(x, base=2):
    try:
        if base == 2:
            return math.sqrt(x)
        else:
            return math.pow(x, 1.0 / float(base))
    except (ValueError, TypeError) as e:
        raise AnsibleFilterTypeError('root() can only be used on numbers: %s' % to_native(e))


def human_readable(size, isbits=False, unit=None):
    ''' Return a human readable string '''
    try:
        return formatters.bytes_to_human(size, isbits, unit)
    except TypeError as e:
        raise AnsibleFilterTypeError("human_readable() failed on bad input: %s" % to_native(e))
    except Exception:
        raise AnsibleFilterError("human_readable() can't interpret following string: %s" % size)


def human_to_bytes(size, default_unit=None, isbits=False):
    ''' Return bytes count from a human readable string '''
    try:
        return formatters.human_to_bytes(size, default_unit, isbits)
    except TypeError as e:
        raise AnsibleFilterTypeError("human_to_bytes() failed on bad input: %s" % to_native(e))
    except Exception:
        raise AnsibleFilterError("human_to_bytes() can't interpret following string: %s" % size)


def rekey_on_member(data, key, duplicates='error'):
    """
    Rekey a dict of dicts on another member

    May also create a dict from a list of dicts.

    duplicates can be one of ``error`` or ``overwrite`` to specify whether to error out if the key
    value would be duplicated or to overwrite previous entries if that's the case.
    """
    if duplicates not in ('error', 'overwrite'):
        raise AnsibleFilterError("duplicates parameter to rekey_on_member has unknown value: {0}".format(duplicates))

    new_obj = {}

    # Ensure the positional args are defined - raise jinja2.exceptions.UndefinedError if not
    bool(data) and bool(key)

    if isinstance(data, Mapping):
        iterate_over = data.values()
    elif isinstance(data, Iterable) and not isinstance(data, (text_type, binary_type)):
        iterate_over = data
    else:
        raise AnsibleFilterTypeError("Type is not a valid list, set, or dict")

    for item in iterate_over:
        if not isinstance(item, Mapping):
            raise AnsibleFilterTypeError("List item is not a valid dict")

        try:
            key_elem = item[key]
        except KeyError:
            raise AnsibleFilterError("Key {0} was not found".format(key))
        except TypeError as e:
            raise AnsibleFilterTypeError(to_native(e))
        except Exception as e:
            raise AnsibleFilterError(to_native(e))

        # Note: if new_obj[key_elem] exists it will always be a non-empty dict (it will at
        # minimum contain {key: key_elem}
        if new_obj.get(key_elem, None):
            if duplicates == 'error':
                raise AnsibleFilterError("Key {0} is not unique, cannot correctly turn into dict".format(key_elem))
            elif duplicates == 'overwrite':
                new_obj[key_elem] = item
        else:
            new_obj[key_elem] = item

    return new_obj


class FilterModule(object):
    ''' Ansible math jinja2 filters '''

    def filters(self):
        filters = {
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
            'zip_longest': itertools.zip_longest,

        }

        return filters
