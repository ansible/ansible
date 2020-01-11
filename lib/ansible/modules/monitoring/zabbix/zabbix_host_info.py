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
hosts:
  description: List of Zabbix hosts. See https://www.zabbix.com/documentation/3.4/manual/api/reference/host/get for list of host values.
  returned: success
  type: dict
  sample: [ { "available": "1", "description": "", "disable_until": "0", "error": "", "flags": "0", "groups": ["1"], "host": "Host A", ... } ]
'''

DOCUMENTATION = r'''
---
module: zabbix_host_info
short_description: Gather information about Zabbix host
description:
   - This module allows you to search for Zabbix host entries.
   - This module was called C(zabbix_host_facts) before Ansible 2.9. The usage did not change.
version_added: "2.7"
author:
    - "Michael Miko (@RedWhiteMiko)"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.4"
options:
    host_name:
        description:
            - Name of the host in Zabbix.
            - host_name is the unique identifier used and cannot be updated using this module.
            - Required when I(host_ip) is not used.
        required: false
        type: str
    host_ip:
        description:
            - Host interface IP of the host in Zabbix.
            - Required when I(host_name) is not used.
        required: false
        type: list
        elements: str
    exact_match:
        description:
            - Find the exact match
        type: bool
        default: no
    remove_duplicate:
        description:
            - Remove duplicate host from host result
        type: bool
        default: yes
    host_inventory:
        description:
            - List of host inventory keys to display in result.
            - Whole host inventory is retrieved if keys are not specified.
        type: list
        elements: str
        required: false
        version_added: 2.8
extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = r'''
- name: Get host info
  local_action:
    module: zabbix_host_info
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    host_name: ExampleHost
    host_ip: 127.0.0.1
    timeout: 10
    exact_match: no
    remove_duplicate: yes

- name: Reduce host inventory information to provided keys
  local_action:
    module: zabbix_host_info
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    host_name: ExampleHost
    host_inventory:
      - os
      - tag
    host_ip: 127.0.0.1
    timeout: 10
    exact_match: no
    remove_duplicate: yes
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

    def get_hosts_by_host_name(self, host_name, exact_match, host_inventory):
        """ Get host by host name """
        search_key = 'search'
        if exact_match:
            search_key = 'filter'
        host_list = self._zapi.host.get({'output': 'extend', 'selectParentTemplates': ['name'], search_key: {'host': [host_name]},
                                         'selectInventory': host_inventory})
        if len(host_list) < 1:
            self._module.fail_json(msg="Host not found: %s" % host_name)
        else:
            return host_list

    def get_hosts_by_ip(self, host_ips, host_inventory):
        """ Get host by host ip(s) """
        hostinterfaces = self._zapi.hostinterface.get({
            'output': 'extend',
            'filter': {
                'ip': host_ips
            }
        })
        if len(hostinterfaces) < 1:
            self._module.fail_json(msg="Host not found: %s" % host_ips)
        host_list = []
        for hostinterface in hostinterfaces:
            host = self._zapi.host.get({
                'output': 'extend',
                'selectGroups': 'extend',
                'selectParentTemplates': ['name'],
                'hostids': hostinterface['hostid'],
                'selectInventory': host_inventory
            })
            host[0]['hostinterfaces'] = hostinterface
            host_list.append(host[0])
        return host_list

    def delete_duplicate_hosts(self, hosts):
        """ Delete duplicated hosts """
        unique_hosts = []
        listed_hostnames = []
        for zabbix_host in hosts:
            if zabbix_host['name'] in listed_hostnames:
                continue
            unique_hosts.append(zabbix_host)
            listed_hostnames.append(zabbix_host['name'])
        return unique_hosts


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            host_name=dict(type='str', default='', required=False),
            host_ip=dict(type='list', default=[], required=False),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', default=10),
            exact_match=dict(type='bool', required=False, default=False),
            remove_duplicate=dict(type='bool', required=False, default=True),
            host_inventory=dict(type='list', default=[], required=False)
        ),
        supports_check_mode=True
    )
    if module._name == 'zabbix_host_facts':
        module.deprecate("The 'zabbix_host_facts' module has been renamed to 'zabbix_host_info'", version='2.13')

    if not HAS_ZABBIX_API:
        module.fail_json(msg=missing_required_lib('zabbix-api', url='https://pypi.org/project/zabbix-api/'), exception=ZBX_IMP_ERR)

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    host_name = module.params['host_name']
    host_ips = module.params['host_ip']
    timeout = module.params['timeout']
    exact_match = module.params['exact_match']
    is_remove_duplicate = module.params['remove_duplicate']
    host_inventory = module.params['host_inventory']

    if not host_inventory:
        host_inventory = 'extend'

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

    if host_name:
        hosts = host.get_hosts_by_host_name(host_name, exact_match, host_inventory)
        if is_remove_duplicate:
            hosts = host.delete_duplicate_hosts(hosts)
        extended_hosts = []
        for zabbix_host in hosts:
            zabbix_host['hostinterfaces'] = host._zapi.hostinterface.get({
                'output': 'extend', 'hostids': zabbix_host['hostid']
            })
            extended_hosts.append(zabbix_host)
        module.exit_json(ok=True, hosts=extended_hosts)

    elif host_ips:
        extended_hosts = host.get_hosts_by_ip(host_ips, host_inventory)
        if is_remove_duplicate:
            hosts = host.delete_duplicate_hosts(extended_hosts)
        module.exit_json(ok=True, hosts=extended_hosts)
    else:
        module.exit_json(ok=False, hosts=[], result="No Host present")


if __name__ == '__main__':
    main()
