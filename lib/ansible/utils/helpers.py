# (c) 2016, Ansible by Red Hat <info@ansible.com>
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

from ansible.errors import AnsibleRuntimeError
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.six import string_types


def pct_to_int(value, num_items, min_value=1):
    '''
    Converts a given value to a percentage if specified as "x%",
    otherwise converts the given value to an integer.
    '''
    if isinstance(value, string_types) and value.endswith('%'):
        value_pct = int(value.replace("%", ""))
        return int((value_pct / 100.0) * num_items) or min_value
    else:
        return int(value)


def object_to_dict(obj, exclude=None):
    """
    Converts an object into a dict making the properties into keys, allows excluding certain keys
    """
    if exclude is None or not isinstance(exclude, list):
        exclude = []
    return dict((key, getattr(obj, key)) for key in dir(obj) if not (key.startswith('_') or key in exclude))


def deduplicate_list(original_list):
    """
    Creates a deduplicated list with the order in which each item is first found.
    """
    seen = set()
    return [x for x in original_list if x not in seen and not seen.add(x)]


def _flatten_list(data):
    if not is_sequence(data):
        raise TypeError('Cannot flatten a {type}'.format(type=type(data)))

    if not data:
        return data

    if is_sequence(data[0]):
        return _flatten_list(data[0] + data[1:])

    try:
        return data[:1] + _flatten_list(data[1:])
    except RecursionError:
        raise AnsibleRuntimeError('List contains too many nested lists')


def string_to_list(string, split=None):
    """Convert a string to a list splitting on ``split``.

    Empty strings will be removed from the returned list.

    If no splitting occurs, return a single item list containing ``string``.
    """

    if split in string:
        # The filter() here removes empty strings from entries such as
        # 'one,'.split(',') --> ['one', '']
        return list(filter(None, string.split(split)))

    return [string]
