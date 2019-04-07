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
module: checkpoint_network_facts
short_description: Get network objects facts on Checkpoint over Web Services API
description:
  - Get network objects facts on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.8"
author: Or Soffer (@Or Soffer)
options:
  name:
    description:
      - Object name. Should be unique in the domain.
    type: str
  uid:
    description:
      - Object unique identifier.
    type: str
  details_level	:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
    default: 'standard'
  limit:
    description:
      - No more than that many results will be returned (1-500).
    type: int
    default: 50
  offset:
    description:
      - Skip that many results before beginning to return them.
    type: int
    default: 0
  order:
    description:
      - Sorts results by the given field. By default the results are sorted in the ascending order by name.
    type: list
  show_membership:
    description:
      - Indicates whether to calculate and show "groups" field for every object in reply.
    type: bool
    default: 'yes'
"""

EXAMPLES = """
- name: Get host object facts
  checkpoint_host_facts:
    name: attacker
"""

RETURN = """
ansible_hosts:
  description: The checkpoint host object facts.
  returned: always.
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, api_call_facts


def main():
    argument_spec = dict(
        name=dict(type='str'),
        uid=dict(type='str'),
        details_level=dict(type='str', choises=['uid', 'standard', 'full']),
        limit=dict(type=int),
        offset=dict(type=int),
        order=dict(type=list),
        show_membership=dict(type=bool)
    )

    user_parameters = list(argument_spec.keys())
    argument_spec.update(checkpoint_argument_spec)
    module = AnsibleModule(argument_spec=argument_spec)
    api_call_object = "network"

    api_call_facts(module, api_call_object, user_parameters)


if __name__ == '__main__':
    main()
