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
module: checkpoint_host_facts
short_description: Get host objects facts on Checkpoint over Web Services API
description:
  - Get host objects facts on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  name:
    description:
      - Name of the host object. If name is not provided, UID is required.
    type: str
  uid:
    description:
      - UID of the host object. If UID is not provided, name is required.
    type: str
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


from ansible.module_utils.network.checkpoint.checkpoint import api_call_facts


def main():
    argument_spec = dict(
        api_call_object=dict(type='str', required=True),
        parameters=dict(type=dict, default={}),
        state=dict(type='str', default='present')
    )
    api_call_facts(argument_spec)


if __name__ == '__main__':
    main()