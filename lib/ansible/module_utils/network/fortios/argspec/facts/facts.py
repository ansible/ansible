#
# -*- coding: utf-8 -*-
# Copyright 2019 Fortinet, Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the fortios monitor module.
"""

CHOICES = [
    'system_current-admins_select',
    'system_firmware_select',
    'system_firmware_upgrade',
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
        'gather_network_resources': dict(requires=False, type='list', choices=CHOICES),
    }
