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
module: ingate_get_rowid
short_description: Get rowid(s) from a table where the columns match.
description:
  - Get rowid(s) from a table where the columns match.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  table:
    description: The name of the table.
    required: true
  columns:
    description: A dict containing column names/values to match.
    required: true
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Get rowid for interface eth0
  ingate_get_rowid:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
    table: network.local_nets
    columns:
      interface: eth0
'''

RETURN = '''
get-rowid:
  description: The matched row id(s).
  returned: success
  type: list
  sample: [1, 3]
'''

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def main():
    argument_spec = ingate_argument_spec(
        table=dict(required=True),
        columns=dict(type='dict', required=True),
    )
    mutually_exclusive = []
    required_if = []
    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    result = dict(changed=False)
    try:
        # Create client and authenticate.
        api_client = ingate_create_client(**module.params)

        # Find matching rowid(s) in a table.
        table = module.params['table']
        columns = module.params['columns']
        response = api_client.dump_table(table)
        rowids = []
        for row in response:
            match = False
            for (name, value) in columns.items():
                if name not in row['data']:
                    continue
                if not row['data'][name] == value:
                    match = False
                    break
                else:
                    match = True
            if match:
                rowids.append(row['id'])
        result.update({'get-rowid': rowids})

    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.network.ingate.common import *

if __name__ == '__main__':
    main()
