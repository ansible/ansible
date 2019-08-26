#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

"""
The arg spec for the fortios monitor module.
"""

CHOICES = [
    'system_current-admins_select',
    'system_firmware_select',
    'system_fortimanager_status',
    'system_ha-checksums_select',
    'system_interface_select',
    'system_status_select',
    'system_time_select',
]


class FactsArgs(object):
    """ The arg spec for the fortios monitor module
    """

    def __init__(self, **kwargs):
        pass

    argument_spec = {
        "host": dict(required=False, type='str'),
        "username": dict(required=False, type='str'),
        "password": dict(required=False, type='str', no_log=True),
        "vdom": dict(required=False, type='str', default="root"),
        "https": dict(required=False, type='bool', default=True),
        "ssl_verify": dict(required=False, type='bool', default=False),
        'gather_subset': dict(requires=True, type='list', choices=CHOICES),
    }
