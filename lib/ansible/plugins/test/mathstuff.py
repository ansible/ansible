# (c) 2016, Ansible, Inc
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import math


def issubset(a, b):
    return set(a) <= set(b)


def issuperset(a, b):
    return set(a) >= set(b)


def isnotanumber(x):
    try:
        return math.isnan(x)
    except TypeError:
        return False


def contains(seq, value):
    '''Opposite of the ``in`` test, allowing use as a test in filters like ``selectattr``

    .. versionadded:: 2.8
    '''
    return value in seq


class TestModule:
    ''' Ansible math jinja2 tests '''

    def tests(self):
        return {
            # set theory
            'issubset': issubset,
            'subset': issubset,
            'issuperset': issuperset,
            'superset': issuperset,
            'contains': contains,

            # numbers
            'isnan': isnotanumber,
            'nan': isnotanumber,
        }
