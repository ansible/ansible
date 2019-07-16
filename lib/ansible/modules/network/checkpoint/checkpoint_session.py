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
module: checkpoint_session
short_description: Manages session objects on Check Point over Web Services API
description:
  - Manages session objects on Check Point devices performing actions like publish and discard.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  uid:
    description:
      - UID of the session.
    type: str
    required: True
  state:
    description:
      - Action to perform on the session object. Valid choices are published and discarded.
    type: str
    choices: ['published', 'discarded']
    default: published
"""

EXAMPLES = """
- name: Publish session
  checkpoint_session:
    uid: 7a13a360-9b24-40d7-acd3-5b50247be33e
    state: published

- name: Discard session
  checkpoint_session:
    uid: 7a13a360-9b24-40d7-acd3-5b50247be33e
    state: discarded
"""

RETURN = """
checkpoint_session:
  description: The checkpoint session output per return from API. It will differ depending on action.
  returned: always.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import publish, discard
import json


def get_session(module, connection):
    payload = {'uid': module.params['uid']}

    code, result = connection.send_request('/web_api/show-session', payload)

    return code, result


def main():
    argument_spec = dict(
        uid=dict(type='str', default=None),
        state=dict(type='str', default='published', choices=['published', 'discarded'])
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_session(module, connection)
    result = {'changed': False}

    if code == 200:
        result['changed'] = True
        payload = None

        if module.params['uid']:
            payload = {'uid': module.params['uid']}

        if module.params['state'] == 'published':
            code, response = connection.send_request('/web_api/publish', payload)
        else:
            code, response = connection.send_request('/web_api/discard', payload)
        if code != 200:
            module.fail_json(msg=response)
        result['checkpoint_session'] = response
    else:
        module.fail_json(msg='Check Point device returned error {0} with message {1}'.format(code, response))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
