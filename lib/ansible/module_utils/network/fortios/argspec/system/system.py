#
# -*- coding: utf-8 -*-
# Copyright 2019 Fortinet, Inc.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The arg spec for the fortios_facts module
"""
from __future__ import absolute_import, division, print_function
__metaclass__ = type


class SystemArgs(object):
    """The arg spec for the fortios_facts module
    """

    FACT_SYSTEM_SUBSETS = frozenset([
        'system_current-admins_select',
        'system_firmware_select',
        'system_fortimanager_status',
        'system_ha-checksums_select',
        'system_interface_select',
        'system_status_select',
        'system_time_select',
    ])

    def __init__(self, **kwargs):
        pass
