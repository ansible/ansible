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
module: checkpoint_object_facts
short_description: Get object facts on Check Point over Web Services API
description:
  - Get object facts on Check Point devices.
    All operations are performed over Web Services API.
version_added: "2.8"
author: "Ansible by Red Hat (@rcarrillocruz)"
options:
  uid:
    description:
      - UID of the object. If UID is not provided, it will do a full search
        which can be filtered with the filter argument.
  object_filter:
    description:
      - Filter expression for search. It accepts AND/OR logical operators and performs a textual
        and IP address search. To search only by IP address, set ip_only argument to True.
        which can be filtered with the filter argument.
  ip_only:
    description:
      - Filter only by IP address.
    type: bool
    default: false
  object_type:
    description:
      - Type of the object to search. Must be a valid API resource name
    type: str
"""

EXAMPLES = """
- name: Get object facts
  checkpoint_object_facts:
    object_filter: 192.168.30.30
    ip_only: yes
"""

RETURN = """
ansible_hosts:
  description: The checkpoint object facts.
  returned: always.
  type: list
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_object(module, connection):
    uid = module.params['uid']
    object_filter = module.params['object_filter']
    ip_only = module.params['ip_only']
    object_type = module.params['object_type']

    if uid:
        payload = {'uid': uid}
        code, result = connection.send_request('/web_api/show-object', payload)
    else:
        payload = {'filter': object_filter, 'ip-only': ip_only, 'type': object_type}
        code, result = connection.send_request('/web_api/show-objects', payload)

    return code, result


def main():
    argument_spec = dict(
        uid=dict(type='str', default=None),
        object_filter=dict(type='str', default=None),
        ip_only=dict(type='bool', default=False),
        object_type=dict(type='str', default=None)
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)

    code, response = get_object(module, connection)

    if code == 200:
        module.exit_json(ansible_facts=dict(checkpoint_objects=response))
    else:
        module.fail_json(msg='Check Point device returned error {0} with message {1}'.format(code, response))


if __name__ == '__main__':
    main()
