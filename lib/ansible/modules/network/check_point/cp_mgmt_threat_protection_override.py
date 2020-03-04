#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
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
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_threat_protection_override
short_description: Edit existing object using object name or uid.
description:
  - Edit existing object using object name or uid.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
  comments:
    description:
      - Protection comments.
    type: str
  follow_up:
    description:
      - Tag the protection with pre-defined follow-up flag.
    type: bool
  overrides:
    description:
      - Overrides per profile for this protection<br> Note, Remove override for Core protections removes only the action's override. Remove override
        for Threat Cloud protections removes the action, track and packet captures.
    type: list
    suboptions:
      action:
        description:
          - Protection action.
        type: str
        choices: ['Threat Cloud: Inactive', 'Detect', 'Prevent <br> Core: Drop', 'Inactive', 'Accept']
      profile:
        description:
          - Profile name.
        type: str
      capture_packets:
        description:
          - Capture packets.
        type: bool
      track:
        description:
          - Tracking method for protection.
        type: str
        choices: ['none', 'log', 'alert', 'mail', 'snmp trap', 'user alert', 'user alert 1', 'user alert 2']
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: threat_protection_override
  cp_mgmt_threat_protection_override:
    name: FTP Commands
    overrides:
    - action: inactive
      capture_packets: true
      profile: New Profile 1
      track: None
    state: present
"""

RETURN = """
cp_mgmt_threat_protection_override:
  description: The checkpoint threat_protection_override output.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        name=dict(type='str'),
        comments=dict(type='str'),
        follow_up=dict(type='bool'),
        overrides=dict(type='list', options=dict(
            action=dict(type='str', choices=['Threat Cloud: Inactive', 'Detect', 'Prevent <br> Core: Drop', 'Inactive', 'Accept']),
            profile=dict(type='str'),
            capture_packets=dict(type='bool'),
            track=dict(type='str', choices=['none', 'log', 'alert', 'mail', 'snmp trap', 'user alert', 'user alert 1', 'user alert 2'])
        )),
        details_level=dict(type='str', choices=['uid', 'standard', 'full'])
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "set-threat-protection"

    result = api_command(module, command)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
