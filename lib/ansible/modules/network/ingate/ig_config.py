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
module: ig_config
short_description: Manage the configuration database on an Ingate SBC.
description:
  - Manage the configuration database on an Ingate SBC.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  add:
    description:
      - Add a row to a table.
    type: bool
  delete:
    description:
      - Delete all rows in a table or a specific row.
    type: bool
  get:
    description:
      - Return all rows in a table or a specific row.
    type: bool
  modify:
    description:
      - Modify a row in a table.
    type: bool
  revert:
    description:
      - Reset the preliminary configuration.
    type: bool
  factory:
    description:
      - Reset the preliminary configuration to its factory defaults.
    type: bool
  store:
    description:
      - Store the preliminary configuration.
    type: bool
  no_response:
    description:
      - Expect no response when storing the preliminary configuration.
        Refer to the C(store) option.
    type: bool
  return_rowid:
    description:
      - Get rowid(s) from a table where the columns match.
    type: bool
  download:
    description:
      - Download the configuration database from the unit.
    type: bool
  store_download:
    description:
      - If the downloaded configuration should be stored on disk.
        Refer to the C(download) option.
    type: bool
    default: false
  path:
    description:
      - Where in the filesystem to store the downloaded configuration.
        Refer to the C(download) option.
  filename:
    description:
      - The name of the file to store the downloaded configuration in.
        Refer to the C(download) option.
  table:
    description:
      - The name of the table.
  rowid:
    description:
      - A row id.
    type: int
  columns:
    description:
      - A dict containing column names/values.
notes:
  - If C(store_download) is set to True, and C(path) and C(filename) is omitted,
    the file will be stored in the current directory with an automatic filename.
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Add/remove DNS servers
  hosts: 192.168.1.1
  connection: local
  vars:
    client_rw:
      version: v1
      address: "{{ inventory_hostname }}"
      scheme: http
      username: alice
      password: foobar
  tasks:

  - name: Load factory defaults
    ig_config:
      client: "{{ client_rw }}"
      factory: true
    register: result
  - debug:
      var: result

  - name: Revert to last known applied configuration
    ig_config:
      client: "{{ client_rw }}"
      revert: true
    register: result
  - debug:
      var: result

  - name: Change the unit name
    ig_config:
      client: "{{ client_rw }}"
      modify: true
      table: misc.unitname
      columns:
        unitname: "Test Ansible"
    register: result
  - debug:
      var: result

  - name: Add a DNS server
    ig_config:
      client: "{{ client_rw }}"
      add: true
      table: misc.dns_servers
      columns:
        server: 192.168.1.21
    register: result
  - debug:
      var: result

  - name: Add a DNS server
    ig_config:
      client: "{{ client_rw }}"
      add: true
      table: misc.dns_servers
      columns:
        server: 192.168.1.22
    register: result
  - debug:
      var: result

  - name: Add a DNS server
    ig_config:
      client: "{{ client_rw }}"
      add: true
      table: misc.dns_servers
      columns:
        server: 192.168.1.23
    register: last_dns
  - debug:
      var: last_dns

  - name: Modify the last added DNS server
    ig_config:
      client: "{{ client_rw }}"
      modify: true
      table: misc.dns_servers
      rowid: "{{ last_dns['add'][0]['id'] }}"
      columns:
        server: 192.168.1.24
    register: result
  - debug:
      var: result

  - name: Return the last added DNS server
    ig_config:
      client: "{{ client_rw }}"
      get: true
      table: misc.dns_servers
      rowid: "{{ last_dns['add'][0]['id'] }}"
    register: result
  - debug:
      var: result

  - name: Remove last added DNS server
    ig_config:
      client: "{{ client_rw }}"
      delete: true
      table: misc.dns_servers
      rowid: "{{ last_dns['add'][0]['id'] }}"
    register: result
  - debug:
      var: result

  - name: Return the all rows from table misc.dns_servers
    ig_config:
      client: "{{ client_rw }}"
      get: true
      table: misc.dns_servers
    register: result
  - debug:
      var: result

  - name: Remove remaining DNS servers
    ig_config:
      client: "{{ client_rw }}"
      delete: true
      table: misc.dns_servers
    register: result
  - debug:
      var: result

  - name: Get rowid for interface eth0
    ig_config:
      client: "{{ client_rw }}"
      return_rowid: true
      table: network.local_nets
      columns:
        interface: eth0
    register: result
  - debug:
      var: result

  - name: Store the preliminary configuration
    ig_config:
      client: "{{ client_rw }}"
      store: true
    register: result
  - debug:
      var: result

  - name: Do backup of the configuration database
    ig_config:
      client: "{{ client_rw }}"
      download: true
      store_download: true
    register: result
  - debug:
      var: result
'''

RETURN = '''
add:
  description: A list containing information about the added row
  returned: when C(add) is yes and success
  type: complex
  contains:
    href:
      description: The REST API URL to the added row
      returned: success
      type: str
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
delete:
  description: A list containing information about the deleted row(s)
  returned: when C(delete) is yes and success
  type: complex
  contains:
    table:
      description: The name of the table
      returned: success
      type: str
      sample: misc.dns_servers
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
get:
  description: A list containing information about the row(s)
  returned: when C(get) is yes and success
  type: complex
  contains:
    table:
      description: The name of the table
      returned: success
      type: str
      sample: Testname
    href:
      description: The REST API URL to the row
      returned: success
      type: str
      sample: http://192.168.1.1/api/v1/misc/dns_servers/1
    data:
      description: Column names/values
      returned: success
      type: complex
      sample: {'number': '2', 'server': '10.48.254.33'}
    id:
      description: The row id
      returned: success
      type: int
      sample: 1
modify:
  description: A list containing information about the modified row
  returned: when C(modify) is yes and success
  type: complex
  contains:
    table:
      description: The name of the table
      returned: success
      type: str
      sample: Testname
    href:
      description: The REST API URL to the modified row
      returned: success
      type: str
      sample: http://192.168.1.1/api/v1/misc/dns_servers/1
    data:
      description: Column names/values
      returned: success
      type: complex
      sample: {'number': '2', 'server': '10.48.254.33'}
    id:
      description: The row id
      returned: success
      type: int
      sample: 10
revert:
  description: A command status message
  returned: when C(revert) is yes and success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: str
      sample: reverted the configuration to the last applied configuration.
factory:
  description: A command status message
  returned: when C(factory) is yes and success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: str
      sample: reverted the configuration to the factory configuration.
store:
  description: A command status message
  returned: when C(store) is yes and success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: str
      sample: Successfully applied and saved the configuration.
return_rowid:
  description: The matched row id(s).
  returned: when C(return_rowid) is yes and success
  type: list
  sample: [1, 3]
download:
  description: Configuration database and meta data
  returned: when C(download) is yes and success
  type: complex
  contains:
    config:
      description: The configuration database
      returned: success
      type: str
    filename:
      description: A suggested name for the configuration
      returned: success
      type: str
      sample: testname_2018-10-01T214040.cfg
    mimetype:
      description: The mimetype
      returned: success
      type: str
      sample: application/x-config-database
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

    if module.params.get('add'):
        # Add a row to a table.
        table = module.params['table']
        columns = module.params['columns']
        response = api_client.add_row(table, **columns)
        return True, 'add', response
    elif module.params.get('delete'):
        # Delete a row/table.
        changed = False
        table = module.params['table']
        rowid = module.params.get('rowid')
        if rowid:
            response = api_client.delete_row(table, rowid=rowid)
        else:
            response = api_client.delete_table(table)
        if response:
            changed = True
        return changed, 'delete', response
    elif module.params.get('get'):
        # Get the contents of a table/row.
        table = module.params['table']
        rowid = module.params.get('rowid')
        if rowid:
            response = api_client.dump_row(table, rowid=rowid)
        else:
            response = api_client.dump_table(table)
        if response:
            changed = True
        return changed, 'get', response
    elif module.params.get('modify'):
        # Modify a table row.
        table = module.params['table']
        columns = module.params['columns']
        rowid = module.params.get('rowid')
        if rowid:
            response = api_client.modify_row(table, rowid=rowid, **columns)
        else:
            response = api_client.modify_single_row(table, **columns)
        if response:
            changed = True
        return changed, 'modify', response
    elif module.params.get('revert'):
        # Revert edits.
        response = api_client.revert_edits()
        if response:
            response = response[0]['revert-edits']
        return True, 'revert', response
    elif module.params.get('factory'):
        # Load factory defaults.
        response = api_client.load_factory()
        if response:
            response = response[0]['load-factory']
        return True, 'factory', response
    elif module.params.get('store'):
        # Store edit.
        no_response = module.params.get('no_response')
        response = api_client.store_edit(no_response=no_response)
        if response:
            response = response[0]['store-edit']
        return True, 'store', response
    elif module.params.get('return_rowid'):
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
        return False, 'return_rowid', rowids
    elif module.params.get('download'):
        # Download the configuration database.
        store = module.params.get('store_download')
        path = module.params.get('path')
        filename = module.params.get('filename')
        response = api_client.download_config(store=store, path=path,
                                              filename=filename)
        if response:
            response = response[0]['download-config']
        return False, 'download', response
    return False, '', {}


def main():
    argument_spec = ingate_argument_spec(
        add=dict(type='bool'),
        delete=dict(type='bool'),
        get=dict(type='bool'),
        modify=dict(type='bool'),
        revert=dict(type='bool'),
        factory=dict(type='bool'),
        store=dict(type='bool'),
        no_response=dict(type='bool', default=False),
        return_rowid=dict(type='bool'),
        download=dict(type='bool'),
        store_download=dict(type='bool', default=False),
        path=dict(),
        filename=dict(),
        table=dict(),
        rowid=dict(type='int'),
        columns=dict(type='dict'),
    )

    mutually_exclusive = [('add', 'delete', 'get', 'modify', 'revert',
                           'factory', 'store', 'return_rowid', 'download')]
    required_one_of = [['add', 'delete', 'get', 'modify', 'revert', 'factory',
                        'store', 'return_rowid', 'download']]
    required_if = [('add', True, ['table', 'columns']),
                   ('delete', True, ['table']),
                   ('get', True, ['table']),
                   ('modify', True, ['table', 'columns']),
                   ('return_rowid', True, ['table', 'columns'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           required_if=required_if,
                           required_one_of=required_one_of,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    result = dict(changed=False)
    try:
        changed, command, response = make_request(module)
        if response and command:
            result[command] = response
        result['changed'] = changed
    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
