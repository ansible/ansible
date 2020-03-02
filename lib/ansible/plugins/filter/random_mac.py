# (c) 2020 Ansible Project
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

import re
from random import Random, SystemRandom

from ansible.errors import AnsibleFilterError
from ansible.module_utils.six import string_types


def random_mac(value, seed=None):
    ''' takes string prefix, and return it completed with random bytes
        to get a complete 6 bytes MAC address '''

    if not isinstance(value, string_types):
        raise AnsibleFilterError('Invalid value type (%s) for random_mac (%s)' %
                                 (type(value), value))

    value = value.lower()
    mac_items = value.split(':')

    if len(mac_items) > 5:
        raise AnsibleFilterError('Invalid value (%s) for random_mac: 5 colon(:) separated'
                                 ' items max' % value)

    err = ""
    for mac in mac_items:
        if not mac:
            err += ",empty item"
            continue
        if not re.match('[a-f0-9]{2}', mac):
            err += ",%s not hexa byte" % mac
    err = err.strip(',')

    if err:
        raise AnsibleFilterError('Invalid value (%s) for random_mac: %s' % (value, err))

    if seed is None:
        r = SystemRandom()
    else:
        r = Random(seed)
    # Generate random int between x1000000000 and xFFFFFFFFFF
    v = r.randint(68719476736, 1099511627775)
    # Select first n chars to complement input prefix
    remain = 2 * (6 - len(mac_items))
    rnd = ('%x' % v)[:remain]
    return value + re.sub(r'(..)', r':\1', rnd)


class FilterModule:
    ''' Ansible jinja2 filters '''
    def filters(self):
        return {
            'random_mac': random_mac,
        }
