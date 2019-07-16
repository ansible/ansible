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
module: checkpoint_task_facts
short_description: Get task objects facts on Checkpoint over Web Services API
description:
  - Get task objects facts on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  task_id:
    description:
      - ID of the task object.
    type: str
    required: True
"""

EXAMPLES = """
- name: Get task facts
  checkpoint_task_facts:
    task_id: 2eec70e5-78a8-4bdb-9a76-cfb5601d0bcb
"""

RETURN = """
ansible_facts:
  description: The checkpoint task facts.
  returned: always.
  type: list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_task(module, connection):
    task_id = module.params['task_id']

    if task_id:
        payload = {'task-id': task_id,
                   'details-level': 'full'}

        code, response = connection.send_request('/web_api/show-task', payload)
    else:
        code, response = connection.send_request('/web_api/show-tasks', None)

    return code, response


def main():
    argument_spec = dict(
        task_id=dict(type='str'),
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_task(module, connection)
    if code == 200:
        module.exit_json(ansible_facts=dict(checkpoint_tasks=response))
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))


if __name__ == '__main__':
    main()
