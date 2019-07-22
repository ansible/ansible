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
module: checkpoint_host
short_description: Manages host objects on Checkpoint over Web Services API
description:
  - Manages host objects on Checkpoint devices including creating, updating, removing access rules objects.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  name:
    description:
      - Name of the access rule.
    type: str
    required: True
  ip_address:
    description:
      - IP address of the host object.
    type: str
  state:
    description:
      - State of the access rule (present or absent). Defaults to present.
    type: str
    default: present
  auto_publish_session:
    description:
      - Publish the current session if changes have been performed
        after task completes.
    type: bool
    default: 'yes'
  auto_install_policy:
    description:
      - Install the package policy if changes have been performed
        after the task completes.
    type: bool
    default: 'yes'
  policy_package:
    description:
      - Package policy name to be installed.
    type: str
    default: 'standard'
  targets:
    description:
      - Targets to install the package policy on.
    type: list
"""

EXAMPLES = """
- name: Create host object
  checkpoint_host:
    name: attacker
    ip_address: 192.168.0.15

- name: Delete host object
  checkpoint_host:
    name: attacker
    state: absent
"""

RETURN = """
checkpoint_hosts:
  description: The checkpoint host object created or updated.
  returned: always, except when deleting the host.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, publish, install_policy
import json


def get_host(module, connection):
    name = module.params['name']

    payload = {'name': name}

    code, response = connection.send_request('/web_api/show-host', payload)

    return code, response


def create_host(module, connection):
    name = module.params['name']
    ip_address = module.params['ip_address']

    payload = {'name': name,
               'ip-address': ip_address}

    code, response = connection.send_request('/web_api/add-host', payload)

    return code, response


def update_host(module, connection):
    name = module.params['name']
    ip_address = module.params['ip_address']

    payload = {'name': name,
               'ip-address': ip_address}

    code, response = connection.send_request('/web_api/set-host', payload)

    return code, response


def delete_host(module, connection):
    name = module.params['name']

    payload = {'name': name}

    code, response = connection.send_request('/web_api/delete-host', payload)

    return code, response


def needs_update(module, host):
    res = False

    if module.params['ip_address'] != host['ipv4-address']:
        res = True

    return res


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        ip_address=dict(type='str'),
        state=dict(type='str', default='present')
    )
    argument_spec.update(checkpoint_argument_spec)

    required_if = [('state', 'present', 'ip_address')]
    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_host(module, connection)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if needs_update(module, response):
                code, response = update_host(module, connection)
                if code != 200:
                    module.fail_json(msg=response)
                if module.params['auto_publish_session']:
                    publish(connection)

                    if module.params['auto_install_policy']:
                        install_policy(connection, module.params['policy_package'], module.params['targets'])

                result['changed'] = True
                result['checkpoint_hosts'] = response
            else:
                pass
        elif code == 404:
            code, response = create_host(module, connection)
            if code != 200:
                module.fail_json(msg=response)
            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
            result['checkpoint_hosts'] = response
    else:
        if code == 200:
            # Handle deletion
            code, response = delete_host(module, connection)
            if code != 200:
                module.fail_json(msg=response)
            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
            result['checkpoint_hosts'] = response
        elif code == 404:
            pass

    result['checkpoint_session_uid'] = connection.get_session_uid()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
