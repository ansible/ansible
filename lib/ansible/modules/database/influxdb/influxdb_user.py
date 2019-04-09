#!/usr/bin/python

# (c) 2017, Vitaliy Zhhuta <zhhuta () gmail.com>
# insipred by Kamil Szczygiel <kamil.szczygiel () intel.com> influxdb_database module
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: influxdb_user
short_description: Manage InfluxDB users
description:
  - Manage InfluxDB users
version_added: 2.5
author: "Vitaliy Zhhuta (@zhhuta)"
requirements:
  - "python >= 2.6"
  - "influxdb >= 0.9"
options:
  user_name:
    description:
      - Name of the user.
    required: True
  user_password:
    description:
      - Password to be set for the user.
    required: false
  admin:
    description:
      - Whether the user should be in the admin role or not.
      - Since version 2.8, the role will also be updated.
    default: no
    type: bool
  state:
    description:
      - State of the user.
    choices: [ present, absent ]
    default: present
  grants:
    description:
      - Privileges to grant to this user. Takes a list of dicts containing the
        "database" and "privilege" keys.
      - If this argument is not provided, the current grants will be left alone.
        If an empty list is provided, all grants for the user will be removed.
    default: None
    version_added: 2.8
extends_documentation_fragment: influxdb
'''

EXAMPLES = '''
- name: Create a user on localhost using default login credentials
  influxdb_user:
    user_name: john
    user_password: s3cr3t

- name: Create a user on localhost using custom login credentials
  influxdb_user:
    user_name: john
    user_password: s3cr3t
    login_username: "{{ influxdb_username }}"
    login_password: "{{ influxdb_password }}"

- name: Create an admin user on a remote host using custom login credentials
  influxdb_user:
    user_name: john
    user_password: s3cr3t
    admin: yes
    hostname: "{{ influxdb_hostname }}"
    login_username: "{{ influxdb_username }}"
    login_password: "{{ influxdb_password }}"

- name: Create a user on localhost with privileges
  influxdb_user:
    user_name: john
    user_password: s3cr3t
    login_username: "{{ influxdb_username }}"
    login_password: "{{ influxdb_password }}"
    grants:
      - database: 'collectd'
        privilege: 'WRITE'
      - database: 'graphite'
        privilege: 'READ'

- name: Destroy a user using custom login credentials
  influxdb_user:
    user_name: john
    login_username: "{{ influxdb_username }}"
    login_password: "{{ influxdb_password }}"
    state: absent
'''

RETURN = '''
#only defaults
'''

import ansible.module_utils.urls
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.influxdb as influx


def find_user(module, client, user_name):
    user_result = None

    try:
        users = client.get_list_users()
        for user in users:
            if user['user'] == user_name:
                user_result = user
                break
    except (ansible.module_utils.urls.ConnectionError, influx.exceptions.InfluxDBClientError) as e:
        module.fail_json(msg=to_native(e))
    return user_result


def check_user_password(module, client, user_name, user_password):
    try:
        client.switch_user(user_name, user_password)
        client.get_list_users()
    except influx.exceptions.InfluxDBClientError as e:
        if e.code == 401:
            return False
    except ansible.module_utils.urls.ConnectionError as e:
        module.fail_json(msg=to_native(e))
    finally:
        # restore previous user
        client.switch_user(module.params['username'], module.params['password'])
    return True


def set_user_password(module, client, user_name, user_password):
    if not module.check_mode:
        try:
            client.set_user_password(user_name, user_password)
        except ansible.module_utils.urls.ConnectionError as e:
            module.fail_json(msg=to_native(e))


def create_user(module, client, user_name, user_password, admin):
    if not module.check_mode:
        try:
            client.create_user(user_name, user_password, admin)
        except ansible.module_utils.urls.ConnectionError as e:
            module.fail_json(msg=to_native(e))


def drop_user(module, client, user_name):
    if not module.check_mode:
        try:
            client.drop_user(user_name)
        except influx.exceptions.InfluxDBClientError as e:
            module.fail_json(msg=e.content)

    module.exit_json(changed=True)


def set_user_grants(module, client, user_name, grants):
    changed = False

    try:
        current_grants = client.get_list_privileges(user_name)
        # Fix privileges wording
        for i, v in enumerate(current_grants):
            if v['privilege'] == 'ALL PRIVILEGES':
                v['privilege'] = 'ALL'
                current_grants[i] = v
            elif v['privilege'] == 'NO PRIVILEGES':
                del(current_grants[i])

        # check if the current grants are included in the desired ones
        for current_grant in current_grants:
            if current_grant not in grants:
                if not module.check_mode:
                    client.revoke_privilege(current_grant['privilege'],
                                            current_grant['database'],
                                            user_name)
                changed = True

        # check if the desired grants are included in the current ones
        for grant in grants:
            if grant not in current_grants:
                if not module.check_mode:
                    client.grant_privilege(grant['privilege'],
                                           grant['database'],
                                           user_name)
                changed = True

    except influx.exceptions.InfluxDBClientError as e:
        module.fail_json(msg=e.content)

    return changed


def main():
    argument_spec = influx.InfluxDb.influxdb_argument_spec()
    argument_spec.update(
        state=dict(default='present', type='str', choices=['present', 'absent']),
        user_name=dict(required=True, type='str'),
        user_password=dict(required=False, type='str', no_log=True),
        admin=dict(default='False', type='bool'),
        grants=dict(type='list')
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    state = module.params['state']
    user_name = module.params['user_name']
    user_password = module.params['user_password']
    admin = module.params['admin']
    grants = module.params['grants']
    influxdb = influx.InfluxDb(module)
    client = influxdb.connect_to_influxdb()
    user = find_user(module, client, user_name)

    changed = False

    if state == 'present':
        if user:
            if not check_user_password(module, client, user_name, user_password) and user_password is not None:
                set_user_password(module, client, user_name, user_password)
                changed = True

            try:
                if admin and not user['admin']:
                    client.grant_admin_privileges(user_name)
                    changed = True
                elif not admin and user['admin']:
                    client.revoke_admin_privileges(user_name)
                    changed = True
            except influx.exceptions.InfluxDBClientError as e:
                module.fail_json(msg=to_native(e))

        else:
            user_password = user_password or ''
            create_user(module, client, user_name, user_password, admin)
            changed = True

        if grants is not None:
            if set_user_grants(module, client, user_name, grants):
                changed = True

        module.exit_json(changed=changed)

    if state == 'absent':
        if user:
            drop_user(module, client, user_name)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
