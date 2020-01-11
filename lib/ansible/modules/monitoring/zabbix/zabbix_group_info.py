#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) me@mimiko.me
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = r'''
---
host_groups:
  description: List of Zabbix groups.
  returned: success
  type: dict
  sample: [ { "flags": "0", "groupid": "33", "internal": "0", "name": "Hostgruup A" } ]
'''

DOCUMENTATION = r'''
---
module: zabbix_group_info
short_description: Gather information about Zabbix hostgroup
description:
   - This module allows you to search for Zabbix hostgroup entries.
   - This module was called C(zabbix_group_facts) before Ansible 2.9. The usage did not change.
version_added: "2.6"
author:
    - "Michael Miko (@RedWhiteMiko)"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.4"
options:
    hostgroup_name:
        description:
            - Name of the hostgroup in Zabbix.
            - hostgroup is the unique identifier used and cannot be updated using this module.
        required: true
        type: list
        elements: str
extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = r'''
- name: Get hostgroup info
  local_action:
    module: zabbix_group_info
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    hostgroup_name:
      - ExampleHostgroup
    timeout: 10
'''


import atexit
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

try:
    from zabbix_api import ZabbixAPI
    HAS_ZABBIX_API = True
except ImportError:
    ZBX_IMP_ERR = traceback.format_exc()
    HAS_ZABBIX_API = False


class Host(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def get_group_ids_by_group_names(self, group_names):
        group_list = self._zapi.hostgroup.get({'output': 'extend', 'filter': {'name': group_names}})
        if len(group_list) < 1:
            self._module.fail_json(msg="Hostgroup not found: %s" % group_names)
        return group_list


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            hostgroup_name=dict(type='list', required=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )
    if module._name == 'zabbix_group_facts':
        module.deprecate("The 'zabbix_group_facts' module has been renamed to 'zabbix_group_info'", version='2.13')

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    hostgroup_name = module.params['hostgroup_name']
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

    host = Host(module, zbx)
    host_groups = host.get_group_ids_by_group_names(hostgroup_name)
    module.exit_json(host_groups=host_groups)


if __name__ == '__main__':
    main()
