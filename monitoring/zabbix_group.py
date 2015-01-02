#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2014, René Moser <mail@renemoser.net>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
module: zabbix_group
short_description: Add or remove a host group to Zabbix.
description:
    - This module uses the Zabbix API to add and remove host groups.
version_added: '1.8'
requirements: [ 'zabbix-api' ]
options:
    state:
        description:
            - Whether the host group should be added or removed.
        required: false
        default: present
        choices: [ 'present', 'absent' ]
    host_group:
        description:
            - Name of the host group to be added or removed.
        required: true
        default: null
        aliases: [ ]
    server_url:
        description:
            - Url of Zabbix server, with protocol (http or https) e.g.
              https://monitoring.example.com/zabbix. C(url) is an alias
              for C(server_url). If not set environment variable
              C(ZABBIX_SERVER_URL) is used.
        required: true
        default: null
        aliases: [ 'url' ]
    login_user:
        description:
            - Zabbix user name. If not set environment variable
              C(ZABBIX_LOGIN_USER) is used.
        required: true
        default: null
    login_password:
        description:
            - Zabbix user password. If not set environment variable
              C(ZABBIX_LOGIN_PASSWORD) is used.
        required: true
notes:
    - The module has been tested with Zabbix Server 2.2.
author: René Moser
'''

EXAMPLES = '''
---
# Add a new host group to Zabbix
- zabbix_group: host_group='Linux servers'
               server_url=https://monitoring.example.com/zabbix
               login_user=ansible
               login_password=secure

# Add a new host group, login data is provided by environment variables:
# ZABBIX_LOGIN_USER, ZABBIX_LOGIN_PASSWORD, ZABBIX_SERVER_URL:
- zabbix_group: host_group=Webservers

# Remove a host group from Zabbix
- zabbix_group: host_group='Linux servers'
               state=absent
               server_url=https://monitoring.example.com/zabbix
               login_user=ansible
               login_password=secure
'''

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


def create_group(zbx, host_group):
    try:
        result = zbx.hostgroup.create(
            {
                'name': host_group
            }
        )
    except BaseException as e:
        return 1, None, str(e)
    return 0, result['groupids'], None


def get_group(zbx, host_group):
    try:
        result = zbx.hostgroup.get(
            {
                'filter':
                {
                    'name': host_group,
                }
            }
        )
    except BaseException as e:
        return 1, None, str(e)

    return 0, result[0]['groupid'], None


def delete_group(zbx, group_id):
    try:
        zbx.hostgroup.delete([ group_id ])
    except BaseException as e:
        return 1, None, str(e)
    return 0, None, None


def check_group(zbx, host_group):
    try:
        result = zbx.hostgroup.exists(
            {
                'name': host_group
            }
        )
    except BaseException as e:
        return 1, None, str(e)
    return 0, result, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent']),
            host_group=dict(required=True, default=None),
            server_url=dict(default=None, aliases=['url']),
            login_user=dict(default=None),
            login_password=dict(default=None),
        ),
        supports_check_mode=True,
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg='Missing requried zabbix-api module (check docs or install with: pip install zabbix-api)')

    try:
        login_user = module.params['login_user'] or os.environ['ZABBIX_LOGIN_USER']
        login_password = module.params['login_password'] or os.environ['ZABBIX_LOGIN_PASSWORD']
        server_url = module.params['server_url'] or os.environ['ZABBIX_SERVER_URL']
    except KeyError, e:
        module.fail_json(msg='Missing login data: %s is not set.' % e.message)

    host_group = module.params['host_group']
    state = module.params['state']

    try:
        zbx = ZabbixAPI(server_url)
        zbx.login(login_user, login_password)
    except BaseException as e:
        module.fail_json(msg='Failed to connect to Zabbix server: %s' % e)

    changed = False
    msg = ''

    if state == 'present':
        (rc, exists, error) = check_group(zbx, host_group)
        if rc != 0:
            module.fail_json(msg='Failed to check host group %s existance: %s' % (host_group, error))
        if not exists:
            if module.check_mode:
                changed = True
            else:
                (rc, group, error) = create_group(zbx, host_group)
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg='Failed to get host group: %s' % error)

    if state == 'absent':
        (rc, exists, error) = check_group(zbx, host_group)
        if rc != 0:
            module.fail_json(msg='Failed to check host group %s existance: %s' % (host_group, error))
        if exists:
            if module.check_mode:
                changed = True
            else:
                (rc, group_id, error) = get_group(zbx, host_group)
                if rc != 0:
                    module.fail_json(msg='Failed to get host group: %s' % error)

                (rc, _, error) = delete_group(zbx, group_id)
                if rc == 0:
                    changed = True
                else:
                    module.fail_json(msg='Failed to remove host group: %s' % error)

    module.exit_json(changed=changed)

from ansible.module_utils.basic import *
main()
