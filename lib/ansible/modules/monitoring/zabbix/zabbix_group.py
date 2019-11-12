#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2013-2014, Epic Games, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_group
short_description: Create/delete Zabbix host groups
description:
   - Create host groups if they do not exist.
   - Delete existing host groups if they exist.
version_added: "1.8"
author:
    - "Cove (@cove)"
    - "Tony Minfei Ding (!UNKNOWN)"
    - "Harrison Gu (@harrisongu)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    state:
        description:
            - Create or delete host group.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
    host_groups:
        description:
            - List of host groups to create or delete.
        required: true
        aliases: [ "host_group" ]

extends_documentation_fragment:
    - zabbix

notes:
    - Too many concurrent updates to the same group may cause Zabbix to return errors, see examples for a workaround if needed.
'''

EXAMPLES = '''
# Base create host groups example
- name: Create host groups
  local_action:
    module: zabbix_group
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    state: present
    host_groups:
      - Example group1
      - Example group2

# Limit the Zabbix group creations to one host since Zabbix can return an error when doing concurrent updates
- name: Create host groups
  local_action:
    module: zabbix_group
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    state: present
    host_groups:
      - Example group1
      - Example group2
  when: inventory_hostname==groups['group_name'][0]
'''


import atexit

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass
    from zabbix_api import Already_Exists

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule


class HostGroup(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # create host group(s) if not exists
    def create_host_group(self, group_names):
        try:
            group_add_list = []
            for group_name in group_names:
                result = self._zapi.hostgroup.get({'filter': {'name': group_name}})
                if not result:
                    try:
                        if self._module.check_mode:
                            self._module.exit_json(changed=True)
                        self._zapi.hostgroup.create({'name': group_name})
                        group_add_list.append(group_name)
                    except Already_Exists:
                        return group_add_list
            return group_add_list
        except Exception as e:
            self._module.fail_json(msg="Failed to create host group(s): %s" % e)

    # delete host group(s)
    def delete_host_group(self, group_ids):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.hostgroup.delete(group_ids)
        except Exception as e:
            self._module.fail_json(msg="Failed to delete host group(s), Exception: %s" % e)

    # get group ids by name
    def get_group_ids(self, host_groups):
        group_ids = []

        group_list = self._zapi.hostgroup.get({'output': 'extend', 'filter': {'name': host_groups}})
        for group in group_list:
            group_id = group['groupid']
            group_ids.append(group_id)
        return group_ids, group_list


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            host_groups=dict(type='list', required=True, aliases=['host_group']),
            state=dict(default="present", choices=['present', 'absent']),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    host_groups = module.params['host_groups']
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    hostGroup = HostGroup(module, zbx)

    group_ids = []
    group_list = []
    if host_groups:
        group_ids, group_list = hostGroup.get_group_ids(host_groups)

    if state == "absent":
        # delete host groups
        if group_ids:
            delete_group_names = []
            hostGroup.delete_host_group(group_ids)
            for group in group_list:
                delete_group_names.append(group['name'])
            module.exit_json(changed=True,
                             result="Successfully deleted host group(s): %s." % ",".join(delete_group_names))
        else:
            module.exit_json(changed=False, result="No host group(s) to delete.")
    else:
        # create host groups
        group_add_list = hostGroup.create_host_group(host_groups)
        if len(group_add_list) > 0:
            module.exit_json(changed=True, result="Successfully created host group(s): %s" % group_add_list)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
