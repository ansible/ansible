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
module: checkpoint_access_rule
short_description: Manages access rules on Check Point over Web Services API
description:
  - Manages access rules on Check Point devices including creating, updating, removing access rules objects,
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  name:
    description:
      - Name of the access rule.
    type: str
  layer:
    description:
      - Layer to attach the access rule to.
    required: True
    type: str
  position:
    description:
      - Position of the access rule.
    type: str
  source:
    description:
      - Source object of the access rule.
    type: str
  destination:
    description:
      - Destination object of the access rule.
    type: str
  action:
    description:
      - Action of the access rule (accept, drop, inform, etc).
    type: str
    default: drop
  enabled:
    description:
      - Enabled or disabled flag.
    type: bool
    default: True
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
- name: Create access rule
  checkpoint_access_rule:
    layer: Network
    name: "Drop attacker"
    position: top
    source: attacker
    destination: Any
    action: Drop

- name: Delete access rule
  checkpoint_access_rule:
    layer: Network
    name: "Drop attacker"
"""

RETURN = """
checkpoint_access_rules:
  description: The checkpoint access rule object created or updated.
  returned: always, except when deleting the access rule.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, publish, install_policy
import json


def get_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']

    payload = {'name': name, 'layer': layer}

    code, response = connection.send_request('/web_api/show-access-rule', payload)

    return code, response


def create_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']
    position = module.params['position']
    source = module.params['source']
    destination = module.params['destination']
    action = module.params['action']

    payload = {'name': name,
               'layer': layer,
               'position': position,
               'source': source,
               'destination': destination,
               'action': action}

    code, response = connection.send_request('/web_api/add-access-rule', payload)

    return code, response


def update_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']
    position = module.params['position']
    source = module.params['source']
    destination = module.params['destination']
    action = module.params['action']
    enabled = module.params['enabled']

    payload = {'name': name,
               'layer': layer,
               'position': position,
               'source': source,
               'destination': destination,
               'action': action,
               'enabled': enabled}

    code, response = connection.send_request('/web_api/set-access-rule', payload)

    return code, response


def delete_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']

    payload = {'name': name,
               'layer': layer,
               }

    code, response = connection.send_request('/web_api/delete-access-rule', payload)

    return code, response


def needs_update(module, access_rule):
    res = False

    if module.params['source'] and module.params['source'] != access_rule['source'][0]['name']:
        res = True
    if module.params['destination'] and module.params['destination'] != access_rule['destination'][0]['name']:
        res = True
    if module.params['action'] != access_rule['action']['name']:
        res = True
    if module.params['enabled'] != access_rule['enabled']:
        res = True

    return res


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        layer=dict(type='str'),
        position=dict(type='str'),
        source=dict(type='str'),
        destination=dict(type='str'),
        action=dict(type='str', default='drop'),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present')
    )
    argument_spec.update(checkpoint_argument_spec)

    required_if = [('state', 'present', ('layer', 'position'))]
    module = AnsibleModule(argument_spec=argument_spec, required_if=required_if)
    connection = Connection(module._socket_path)
    code, response = get_access_rule(module, connection)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if needs_update(module, response):
                code, response = update_access_rule(module, connection)
                if code != 200:
                    module.fail_json(msg=response)
                if module.params['auto_publish_session']:
                    publish(connection)

                    if module.params['auto_install_policy']:
                        install_policy(connection, module.params['policy_package'], module.params['targets'])

                result['changed'] = True
                result['checkpoint_access_rules'] = response
            else:
                pass
        elif code == 404:
            code, response = create_access_rule(module, connection)
            if code != 200:
                module.fail_json(msg=response)
            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
            result['checkpoint_access_rules'] = response
    else:
        if code == 200:
            code, response = delete_access_rule(module, connection)
            if code != 200:
                module.fail_json(msg=response)
            if module.params['auto_publish_session']:
                publish(connection)

                if module.params['auto_install_policy']:
                    install_policy(connection, module.params['policy_package'], module.params['targets'])

            result['changed'] = True
            result['checkpoint_access_rules'] = response
        elif code == 404:
            pass

    result['checkpoint_session_uid'] = connection.get_session_uid()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
