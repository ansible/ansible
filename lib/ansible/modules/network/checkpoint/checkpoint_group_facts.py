#!/usr/bin/python
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
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: checkpoint_group_facts
short_description: Get group objects facts on Checkpoint over Web Services API
description:
  - Get group objects facts on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  show_as_ranges:
    description:
      - When true, the group's matched content is displayed as ranges of IP addresses rather than network objects.
        Objects that are not represented using IP addresses are presented as objects.
        The 'members' parameter is omitted from the response and instead the 'ranges' parameter is displayed.
    type: bool
  dereference_group_members:
    description:
      - Indicates whether to dereference "members" field by details level for every object in reply.
    type: bool
extends_documentation_fragment: checkpoint_facts
"""

EXAMPLES = """
- name: Get group object facts
  checkpoint_group_facts:
    name: "New Group 1"
"""

RETURN = """
api_result:
  description: The checkpoint object facts.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_facts, api_call_facts


def main():
    argument_spec = dict(
        show_as_ranges=dict(type='bool'),
        dereference_group_members=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_facts)

    module = AnsibleModule(argument_spec=argument_spec)

    api_call_object = "group"
    api_call_object_plural_version = "groups"

    api_call_facts(module, api_call_object, api_call_object_plural_version)


if __name__ == '__main__':
    main()
