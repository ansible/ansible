#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013-2014, Epic Games, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_hostmacro
short_description: Create/update/delete Zabbix host macros
description:
   - manages Zabbix host macros, it can create, update or delete them.
version_added: "2.0"
author:
    - "Cove (@cove)"
    - Dean Hailin Song (!UNKNOWN)
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    host_name:
        description:
            - Name of the host.
        required: true
    macro_name:
        description:
            - Name of the host macro without the enclosing curly braces and the leading dollar sign.
        required: true
    macro_value:
        description:
            - Value of the host macro.
        required: true
    state:
        description:
            - State of the macro.
            - On C(present), it will create if macro does not exist or update the macro if the associated data is different.
            - On C(absent) will remove a macro if it exists.
        required: false
        choices: ['present', 'absent']
        default: "present"
    force:
        description:
            - Only updates an existing macro if set to C(yes).
        default: 'yes'
        type: bool
        version_added: 2.5

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
- name: Create a new host macro or update an existing macro's value
  local_action:
    module: zabbix_hostmacro
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    host_name: ExampleHost
    macro_name: EXAMPLE.MACRO
    macro_value: Example value
    state: present
'''


import atexit

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    # Extend the ZabbixAPI
    # Since the zabbix-api python module too old (version 1.0, no higher version so far).
    class ZabbixAPIExtends(ZabbixAPI):
        def __init__(self, server, timeout, user, passwd, validate_certs, **kwargs):
            ZabbixAPI.__init__(self, server, timeout=timeout, user=user, passwd=passwd, validate_certs=validate_certs)

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule


class HostMacro(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # get host id by host name
    def get_host_id(self, host_name):
        try:
            host_list = self._zapi.host.get({'output': 'extend', 'filter': {'host': host_name}})
            if len(host_list) < 1:
                self._module.fail_json(msg="Host not found: %s" % host_name)
            else:
                host_id = host_list[0]['hostid']
                return host_id
        except Exception as e:
            self._module.fail_json(msg="Failed to get the host %s id: %s." % (host_name, e))

    # get host macro
    def get_host_macro(self, macro_name, host_id):
        try:
            host_macro_list = self._zapi.usermacro.get(
                {"output": "extend", "selectSteps": "extend", 'hostids': [host_id], 'filter': {'macro': '{$' + macro_name + '}'}})
            if len(host_macro_list) > 0:
                return host_macro_list[0]
            return None
        except Exception as e:
            self._module.fail_json(msg="Failed to get host macro %s: %s" % (macro_name, e))

    # create host macro
    def create_host_macro(self, macro_name, macro_value, host_id):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.usermacro.create({'hostid': host_id, 'macro': '{$' + macro_name + '}', 'value': macro_value})
            self._module.exit_json(changed=True, result="Successfully added host macro %s" % macro_name)
        except Exception as e:
            self._module.fail_json(msg="Failed to create host macro %s: %s" % (macro_name, e))

    # update host macro
    def update_host_macro(self, host_macro_obj, macro_name, macro_value):
        host_macro_id = host_macro_obj['hostmacroid']
        if host_macro_obj['macro'] == '{$' + macro_name + '}' and host_macro_obj['value'] == macro_value:
            self._module.exit_json(changed=False, result="Host macro %s already up to date" % macro_name)
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.usermacro.update({'hostmacroid': host_macro_id, 'value': macro_value})
            self._module.exit_json(changed=True, result="Successfully updated host macro %s" % macro_name)
        except Exception as e:
            self._module.fail_json(msg="Failed to update host macro %s: %s" % (macro_name, e))

    # delete host macro
    def delete_host_macro(self, host_macro_obj, macro_name):
        host_macro_id = host_macro_obj['hostmacroid']
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.usermacro.delete([host_macro_id])
            self._module.exit_json(changed=True, result="Successfully deleted host macro %s" % macro_name)
        except Exception as e:
            self._module.fail_json(msg="Failed to delete host macro %s: %s" % (macro_name, e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            host_name=dict(type='str', required=True),
            macro_name=dict(type='str', required=True),
            macro_value=dict(type='str', required=True),
            state=dict(default="present", choices=['present', 'absent']),
            timeout=dict(type='int', default=10),
            force=dict(type='bool', default=True)
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
    host_name = module.params['host_name']
    macro_name = (module.params['macro_name'])
    macro_value = module.params['macro_value']
    state = module.params['state']
    timeout = module.params['timeout']
    force = module.params['force']

    if ':' in macro_name:
        macro_name = ':'.join([macro_name.split(':')[0].upper(), ':'.join(macro_name.split(':')[1:])])
    else:
        macro_name = macro_name.upper()

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPIExtends(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                               validate_certs=validate_certs)
        zbx.login(login_user, login_password)
        atexit.register(zbx.logout)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    host_macro_class_obj = HostMacro(module, zbx)

    if host_name:
        host_id = host_macro_class_obj.get_host_id(host_name)
        host_macro_obj = host_macro_class_obj.get_host_macro(macro_name, host_id)

    if state == 'absent':
        if not host_macro_obj:
            module.exit_json(changed=False, msg="Host Macro %s does not exist" % macro_name)
        else:
            # delete a macro
            host_macro_class_obj.delete_host_macro(host_macro_obj, macro_name)
    else:
        if not host_macro_obj:
            # create host macro
            host_macro_class_obj.create_host_macro(macro_name, macro_value, host_id)
        elif force:
            # update host macro
            host_macro_class_obj.update_host_macro(host_macro_obj, macro_name, macro_value)
        else:
            module.exit_json(changed=False, result="Host macro %s already exists and force is set to no" % macro_name)


if __name__ == '__main__':
    main()
