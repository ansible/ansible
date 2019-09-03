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
module: checkpoint_run_script
short_description: Run scripts on Check Point devices over Web Services API
description:
  - Run scripts on Check Point devices.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  script_name:
    description:
      - Name of the script.
    type: str
    required: True
  script:
    description:
      - Script body contents.
    type: str
    required: True
  targets:
    description:
      - Targets the script should be run against. Can reference either name or UID.
    type: list
    required: True
"""

EXAMPLES = """
- name: Run script
  checkpoint_run_script:
    script_name: "List root"
    script: ls -l /
    targets:
      - mycheckpointgw
"""

RETURN = """
checkpoint_run_script:
  description: The checkpoint run script output.
  returned: always.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import publish, install_policy
import json


def run_script(module, connection):
    script_name = module.params['script_name']
    script = module.params['script']
    targets = module.params['targets']

    payload = {'script-name': script_name,
               'script': script,
               'targets': targets}

    code, response = connection.send_request('/web_api/run-script', payload)

    return code, response


def main():
    argument_spec = dict(
        script_name=dict(type='str', required=True),
        script=dict(type='str', required=True),
        targets=dict(type='list', required=True)
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = run_script(module, connection)
    result = {'changed': True}

    if code == 200:
        result['checkpoint_run_script'] = response
    else:
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
