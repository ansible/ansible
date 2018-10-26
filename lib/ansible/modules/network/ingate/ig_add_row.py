#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ig_add_row
short_description: Add a row to a table on an Ingate SBC.
description:
  - Add a row to a table on an Ingate SBC.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  table:
    description: The name of the table.
    required: true
  columns:
    description: A dict containing column names/values.
    required: true
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Add a row to a table
  ig_add_row:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    table: misc.dns_servers
    columns:
      server: 10.48.254.21
'''

RETURN = '''
add-row:
  description: Information about the added row
  returned: success
  type: complex
  contains:
    href:
      description: The REST API URL to the added row
      returned: success
      type: string
      sample: http://192.168.1.1/api/v1/misc/dns_servers/2
    data:
      description: Column names/values
      returned: success
      type: complex
      sample: {'number': '2', 'server': '10.48.254.33'}
    id:
      description: The row id
      returned: success
      type: int
      sample: 22
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ingate.common import (ingate_argument_spec,
                                                        ingate_create_client)

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def make_request(module):
    # Create client and authenticate.
    api_client = ingate_create_client(**module.params)

    # Add a row to a table.
    table = module.params['table']
    columns = module.params['columns']
    response = api_client.add_row(table, **columns)
    return response


def main():
    argument_spec = ingate_argument_spec(
        table=dict(required=True),
        columns=dict(type='dict', required=True),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    result = dict(changed=False)
    try:
        response = make_request(module)
        result.update({'add-row': response[0]})
        result['changed'] = True
    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
