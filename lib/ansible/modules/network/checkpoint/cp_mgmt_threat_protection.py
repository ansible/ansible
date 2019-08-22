#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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
module: cp_mgmt_threat_protection
short_description: Manages threat-protection objects on Checkpoint over Web Services API
description:
  - Manages threat-protection objects on Checkpoint devices including creating, updating and removing objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
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
      - Overrides per profile for this protection<br> Note, Remove override for Core protections removes only the action’s override. Remove override
        for Threat Cloud protections removes the action, track and packet captures.
    type: list
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  package_format:
    description:
      - Protections package format.
    type: str
    choices: ['snort']
  package_path:
    description:
      - Protections package path.
    type: str
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: set-threat-protection
  cp_mgmt_threat_protection:
    name: FTP Commands
    overrides:
      remove:
      - New profile 1

- name: add-threat-protections
  cp_mgmt_threat_protection:
    package_format: snort
    package_path: /path/to/community.rules

- name: delete-threat-protections
  cp_mgmt_threat_protection:
    package_format: snort
    state: absent
"""

RETURN = """
cp_mgmt_threat_protection:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        comments=dict(type='str'),
        follow_up=dict(type='bool'),
        overrides=dict(type='list'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        package_format=dict(type='str', choices=['snort']),
        package_path=dict(type='str')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'threat-protection'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
