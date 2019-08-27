#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communictions Cloud Infrastructure Services
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Ken Sinfield (@kensinfield)
#
# Object Helper functions to keep modules clean

from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.ntt_mcp.ntt_mcp_utils import compare_json

def fw_update_dict(fw_rule):
    """
    Modify the firewall rule dict to match the correct schema

    :arg fw_rule: firewall rule dict
    :returns: The updated firewall rule dict
    """
    fw_rule.pop('placement', None)
    fw_rule.pop('ipVersion', None)
    fw_rule.pop('name', None)
    fw_rule.pop('id', None)
    return fw_rule

def compare_fw_rule(new_fw_rule, existing_fw_rule):
    """
    Compare two firewall rules and return any differences. This uses the generic
    compare_json but first the schemas of the firewall rules must be matched

    :arg new_fw_rule: The new firewall rule to check
    :arg existing_fw_rule: The existing firewall rule to check against
    :returns: dict containing any differences
    """
    existing_dst = existing_fw_rule['destination']
    existing_src = existing_fw_rule['source']
    existing_fw_rule['destination'] = {}
    existing_fw_rule['source'] = {}

    # Handle schema differences between create/update schema and the returned get/list schema
    if 'ipAddressList' in existing_dst:
        existing_fw_rule['destination']['ipAddressListId'] = existing_dst['ipAddressList']['id']
    if 'portList' in existing_dst:
        existing_fw_rule['destination']['portListId'] = existing_dst['portList']['id']
    if 'ipAddressList' in existing_src:
        existing_fw_rule['source']['ipAddressListId'] = existing_src['ipAddressList']['id']
    if 'portList' in existing_src:
        existing_fw_rule['source']['portListId'] = existing_src['portList']['id']

    existing_fw_rule.pop('ruleType', None)
    existing_fw_rule.pop('datacenterId', None)
    existing_fw_rule.pop('state', None)
    new_fw_rule.pop('placement', None)

    return compare_json(new_fw_rule, existing_fw_rule, None)
