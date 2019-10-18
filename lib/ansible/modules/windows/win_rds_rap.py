#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Subileau (@ksubileau)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_rds_rap
short_description: Manage Resource Authorization Policies (RAP) on a Remote Desktop Gateway server
description:
  - Creates, removes and configures a Remote Desktop resource authorization policy (RD RAP).
  - A RD RAP allows you to specify the network resources (computers) that users can connect
    to remotely through a Remote Desktop Gateway server.
version_added: "2.8"
author:
  - Kevin Subileau (@ksubileau)
options:
  name:
    description:
      - Name of the resource authorization policy.
    required: yes
  state:
    description:
      - The state of resource authorization policy.
      - If C(absent) will ensure the policy is removed.
      - If C(present) will ensure the policy is configured and exists.
      - If C(enabled) will ensure the policy is configured, exists and enabled.
      - If C(disabled) will ensure the policy is configured, exists, but disabled.
    type: str
    choices: [ absent, disabled, enabled, present ]
    default: present
  description:
    description:
      - Optional description of the resource authorization policy.
    type: str
  user_groups:
    description:
      - List of user groups that are associated with this resource authorization policy (RAP).
        A user must belong to one of these groups to access the RD Gateway server.
      - Required when a new RAP is created.
    type: list
  allowed_ports:
    description:
      - List of port numbers through which connections are allowed for this policy.
      - To allow connections through any port, specify 'any'.
    type: list
  computer_group_type:
    description:
      - 'The computer group type:'
      - 'C(rdg_group): RD Gateway-managed group'
      - 'C(ad_network_resource_group): Active Directory Domain Services network resource group'
      - 'C(allow_any): Allow users to connect to any network resource.'
    type: str
    choices: [ rdg_group, ad_network_resource_group, allow_any ]
  computer_group:
    description:
      - The computer group name that is associated with this resource authorization policy (RAP).
      - This is required when I(computer_group_type) is C(rdg_group) or C(ad_network_resource_group).
    type: str
requirements:
  - Windows Server 2008R2 (6.1) or higher.
  - The Windows Feature "RDS-Gateway" must be enabled.
seealso:
- module: win_rds_cap
- module: win_rds_rap
- module: win_rds_settings
'''

EXAMPLES = r'''
- name: Create a new RDS RAP
  win_rds_rap:
    name: My RAP
    description: Allow all users to connect to any resource through ports 3389 and 3390
    user_groups:
      - BUILTIN\users
    computer_group_type: allow_any
    allowed_ports:
      - 3389
      - 3390
    state: enabled
'''

RETURN = r'''
'''
