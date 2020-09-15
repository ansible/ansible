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
module: checkpoint_access_rule_facts
short_description: Get access rules objects facts on Check Point over Web Services API
description:
  - Get access rules objects facts on Check Point devices.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  name:
    description:
      - Name of the access rule. If not provided, UID is required.
    type: str
  uid:
    description:
      - UID of the access rule. If not provided, name is required.
    type: str
  layer:
    description:
      - Layer the access rule is attached to.
    required: True
    type: str
"""

EXAMPLES = """
- name: Get access rule facts
  checkpoint_access_rule_facts:
    layer: Network
    name: "Drop attacker"
"""

RETURN = """
ansible_facts:
  description: The checkpoint access rule object facts.
  returned: always.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_access_rule(module, connection):
    name = module.params['name']
    uid = module.params['uid']
    layer = module.params['layer']

    if uid:
        payload = {'uid': uid, 'layer': layer}
    elif name:
        payload = {'name': name, 'layer': layer}

    code, response = connection.send_request('/web_api/show-access-rule', payload)

    return code, response


def main():
    argument_spec = dict(
        name=dict(type='str'),
        uid=dict(type='str'),
        layer=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_access_rule(module, connection)
    if code == 200:
        module.exit_json(ansible_facts=dict(checkpoint_access_rules=response))
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))


if __name__ == '__main__':
    main()
