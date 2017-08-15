#!/usr/bin/python

# (c) 2016, Kamil Szczygiel <kamil.szczygiel () intel.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: influxdb_database
short_description: Manage InfluxDB databases
description:
    - Manage InfluxDB databases
version_added: 2.1
author: "Kamil Szczygiel (@kamsz)"
requirements:
    - "python >= 2.6"
    - "influxdb >= 0.9"
options:
    hostname:
        description:
            - The hostname or IP address on which InfluxDB server is listening
        required: true
    username:
        description:
            - Username that will be used to authenticate against InfluxDB server
        default: root
        required: false
    password:
        description:
            - Password that will be used to authenticate against InfluxDB server
        default: root
        required: false
    port:
        description:
            - The port on which InfluxDB server is listening
        default: 8086
        required: false
    database_name:
        description:
            - Name of the database that will be created/destroyed
        required: true
    state:
        description:
            - Determines if the database should be created or destroyed
        choices: ['present', 'absent']
        default: present
        required: false
'''

EXAMPLES = '''
# Example influxdb_database command from Ansible Playbooks
- name: Create database
  influxdb_database:
      hostname: "{{influxdb_ip_address}}"
      database_name: "{{influxdb_database_name}}"
      state: present

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
      state: present
'''

RETURN = '''
#only defaults
'''

try:
    import requests.exceptions
    from influxdb import InfluxDBClient
    from influxdb import exceptions
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False

from ansible.module_utils.basic import AnsibleModule


def influxdb_argument_spec():
    return dict(
        hostname=dict(required=True, type='str'),
        port=dict(default=8086, type='int'),
        username=dict(default='root', type='str'),
        password=dict(default='root', type='str', no_log=True),
        database_name=dict(required=True, type='str')
    )


def connect_to_influxdb(module):
    hostname = module.params['hostname']
    port = module.params['port']
    username = module.params['username']
    password = module.params['password']
    database_name = module.params['database_name']

    client = InfluxDBClient(
        host=hostname,
        port=port,
        username=username,
        password=password,
        database=database_name
    )
    return client


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
    argument_spec = influxdb_argument_spec()
    argument_spec.update(
        state=dict(default='present', type='str', choices=['present', 'absent'])
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_INFLUXDB:
        module.fail_json(msg='influxdb python package is required for this module')

    state = module.params['state']
    database_name = module.params['database_name']

    client = connect_to_influxdb(module)
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
