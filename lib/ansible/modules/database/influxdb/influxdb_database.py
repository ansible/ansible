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
short_description: Manage InfluxDB databases.
description:
    - Manage InfluxDB databases.
version_added: 2.1
author: "Kamil Szczygiel (@kamsz)"
requirements:
    - "python >= 2.6"
    - "influxdb >= 0.9"
options:
    hostname:
        description:
            - The hostname or IP address on which InfluxDB server is listening.
        required: true
    username:
        description:
            - Username that will be used to authenticate against InfluxDB server.
        default: root
    password:
        description:
            - Password that will be used to authenticate against InfluxDB server.
        default: root
    port:
        description:
            - The port on which InfluxDB server is listening.
        default: 8086
    database_name:
        description:
            - Name of the database that will be created/destroyed.
        required: true
    state:
        description:
            - Determines if the database should be created or destroyed.
        choices: [ present, absent ]
        default: present
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
# only defaults
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.database.influxdb import (
    influxdb_argument_spec,
    AnsibleInfluxDB
)


class AnsibleInfluxDBDatabase(AnsibleInfluxDB):

    def create_database(self, database_name):
        client = self.connect()
        if not self.module.check_mode:
            try:
                client.create_database(database_name)
            except Exception as e:
                self.module.fail_json(msg=to_native(e))
        self.module.exit_json(changed=True)

    def drop_database(self, database_name):
        client = self.connect()
        if not self.module.check_mode:
            try:
                client.drop_database(database_name)
            except Exception as e:
                self.module.fail_json(msg=to_native(e))
        self.module.exit_json(changed=True)

    def find_database(self, database_name):
        client = self.connect()
        database = None
        try:
            databases = client.get_list_database()
            for db in databases:
                if db['name'] == database_name:
                    database = db
                    break
        except Exception as e:
            self.module.fail_json(msg=to_native(e))
        return database


def main():
    argument_spec = influxdb_argument_spec()
    argument_spec.update(
        state=dict(default='present', type='str', choices=['present', 'absent'])
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    influx = AnsibleInfluxDBDatabase(module)

    state = module.params['state']
    database_name = module.params['database_name']

    database = influx.find_database(database_name)
    if state == 'present':
        if database:
            module.exit_json(changed=False)
        else:
            influx.create_database(database_name)

    if state == 'absent':
        if database:
            influx.drop_database(database_name)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
