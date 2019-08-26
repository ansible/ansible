#
# -*- coding: utf-8 -*-
# Copyright 2019 Fortinet, Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the nxos_lacp module
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type


class SystemArgs(object):
    """The arg spec for the fortios_facts module
    """

    def __init__(self, **kwargs):
        pass

    system_interface_select_spec = {
        "system_interface_select": {
            "required": False, "type": "dict",
             "options": {
                 "interface_name": {"required": False, "type": "str"},
                 "include_vlan": {"required": False, "type": "bool"}
             }
        }
    }
