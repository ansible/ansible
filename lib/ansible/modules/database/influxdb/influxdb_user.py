#!/usr/bin/python

# (c) 2016, Adam Hamsik <haaaad () gmail.com>
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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: influxdb_user
short_description: Manage InfluxDB users
description:
    - Manage InfluxDB users
version_added: 2.3
author: "Adam Hamsik (@haad)"
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
            - Database name to work with.
        required: true
    user_name:
        description:
            - Name of the user that will be created/destroyed.
        required: true
    user_pass:
        description:
            - User password to create.
        required: true
    user_admin:
        description:
            - Determine if created user will be admin or not.
    state:
        description:
            - Determines if the user should be created or destroyed.
        choices: ['present', 'absent']
        default: present
'''

EXAMPLES = '''
# Example influxdb_user command from Ansible Playbooks
- name: Create user
  influxdb_user:
    database_name: influx
    hostname: "{{ influxdb_ip_address }}"
    user_name: "{{ influxdb_user_name }}"
    user_pass: "{{ influxdb_user_pass }}"
    user_admin: no
    state: present

- name: Destroy user
  influxdb_user:
    database_name: influx
    hostname: "{{ influxdb_ip_address }}"
    user_name: "{{ influxdb_user_name }}"
    state: absent

- name: Create admin user
  influxdb_user:
    database_name: influx
    hostname: "{{ influxdb_ip_address }}"
    username: "{{ influxdb_username }}"
    password: "{{ influxdb_password }}"
    user_name: "{{ influxdb_user_name }}"
    user_pass: "{{ influxdb_user_pass }}"
    user_admin: yes
    state: present
'''

RETURN = '''
#only defaults
'''

try:
    from influxdb import InfluxDBClient
    from influxdb import exceptions
    from requests.exceptions import ConnectionError
    HAS_INFLUXDB = True
except ImportError:
    HAS_INFLUXDB = False

from ansible.module_utils.basic import AnsibleModule

def influxdb_argument_spec():
    return dict(
        hostname=dict(required=True, type='str'),
        port=dict(default=8086, type='int'),
        database_name=dict(required=True, type='str'),
        username=dict(default='root', type='str'),
        password=dict(default='root', type='str', no_log=True),
        user_name=dict(required=True, type='str'),
        user_pass=dict(required=True, type='str', no_log=True),
        user_admin=dict(required=False, default=False, type='bool')
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


def find_user(module, client, user_name):
    u = None

    try:
        users = client.get_list_users()
        for user in users:
            if user['user'] == user_name:
                u = user
                break
    except ConnectionError as e:
        module.fail_json(msg=str(e))
    return u

def create_user(module, client, user_name, user_pass, user_admin):
    if not module.check_mode:
        try:
            client.create_user(user_name, user_pass, user_admin)
        except ConnectionError as e:
            module.fail_json(msg=str(e))

    module.exit_json(changed=True)

def drop_user(module, client, user_name):
    if not module.check_mode:
        try:
            client.drop_user(user_name)
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
    user_name = module.params['user_name']
    user_pass = module.params['user_pass']
    user_admin = module.params['user_admin']

    try:
        client = connect_to_influxdb(module)
        user = find_user(module, client, user_name)

        if state == 'present':
            if user:
                module.exit_json(changed=False)
            else:
                create_user(module, client, user_name, user_pass, user_admin)

        if state == 'absent':
            if user:
                drop_user(module, client, user_name)
            else:
                module.exit_json(changed=False)
    except Exception as e:
        module.fail_json(msg="{}: {}".format(e.__class__.__name__, str(e)))

if __name__ == '__main__':
    main()
