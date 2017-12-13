#!/usr/bin/python

# (c) 2016, Kamil Szczygiel <kamil.szczygiel () intel.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: influxdb_database
short_description: Manage InfluxDB databases
description:
    - Manage InfluxDB databases.
version_added: 2.1
author: "Kamil Szczygiel (@kamsz)"
requirements:
    - "python >= 2.6"
    - "influxdb >= 0.9"
    - requests
options:
    state:
        description:
            - Determines if the database should be created or destroyed.
        choices: [ present, absent ]
        default: present
extends_documentation_fragment: influxdb
'''

EXAMPLES = '''
# Example influxdb_database command from Ansible Playbooks
- name: Create database
  influxdb_database:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"

- name: Destroy database
  influxdb_database:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      state: absent

- name: Create database using custom credentials
  influxdb_database:
      hostname: "{{influxdb_ip_address}}"
      username: "{{influxdb_username}}"
      password: "{{influxdb_password}}"
      database_name: "{{influxdb_database_name}}"
      ssl: yes
      validate_certs: yes
'''

RETURN = '''
# only defaults
'''

try:
    import requests.exceptions
    from influxdb import exceptions
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.influxdb import InfluxDb


def find_database(module, client, database_name):
    database = None

    try:
        databases = client.get_list_database()
        for db in databases:
            if db['name'] == database_name:
                database = db
                break
    except requests.exceptions.ConnectionError as e:
        module.fail_json(msg=str(e))
    return database


def create_database(module, client, database_name):
    if not module.check_mode:
        try:
            client.create_database(database_name)
        except requests.exceptions.ConnectionError as e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=True)


def drop_database(module, client, database_name):
    if not module.check_mode:
        try:
            client.drop_database(database_name)
        except exceptions.InfluxDBClientError as e:
            module.fail_json(msg=e.content)

    module.exit_json(changed=True)


def main():
    argument_spec = InfluxDb.influxdb_argument_spec()
    argument_spec.update(
        state=dict(default='present', type='str', choices=['present', 'absent'])
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params['state']

    influxdb = InfluxDb(module)
    client = influxdb.connect_to_influxdb()
    database_name = influxdb.database_name
    database = find_database(module, client, database_name)

    if state == 'present':
        if database:
            module.exit_json(changed=False)
        else:
            create_database(module, client, database_name)

    if state == 'absent':
        if database:
            drop_database(module, client, database_name)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
