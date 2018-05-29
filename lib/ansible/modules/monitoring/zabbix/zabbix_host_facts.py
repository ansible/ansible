#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) me@mimiko.me
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

RETURN = '''
---
hosts:
  description: List of Zabbix host. See https://www.zabbix.com/documentation/3.4/manual/api/reference/host/get for list of host values.
  returned: success
  type: dict
  sample: [ { "available": "1", "description": "", "disable_until": "0", "error": "", "flags": "0", "groups": ["1"], "host": "Host A", ... } ]
'''

DOCUMENTATION = '''
---
module: zabbix_host_facts
short_description: Gather facts about Zabbix host
description:
   - This module allows you to search for Zabbix host entries.
version_added: "2.7"
author:
    - "(@redwhitemiko)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    server_url:
        description:
            - Url of Zabbix server, with protocol (http or https).
        required: true
        aliases: [ "url" ]
    login_user:
        description:
            - Zabbix user name, used to authenticate against the server.
        required: true
    login_password:
        description:
            - Zabbix user password.
        required: true
    http_login_user:
        description:
            - Basic Auth login.
        required: false
        default: null
    http_login_password:
        description:
            - Basic Auth password.
        required: false
        default: null
    host_name:
        description:
            - Name of the host in Zabbix.
            - host_name is the unique identifier used and cannot be updated using this module.
        required: true
    host_ip:
        description:
            - Host interface IP of the host in Zabbix.
        required: false
    timeout:
        description:
            - The timeout of API request (seconds).
        default: 10
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
'''

EXAMPLES = '''
- name: Get host info
  local_action:
    module: zabbix_host_facts
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    host_name: ExampleHost
    host_ip: 127.0.0.1
    timeout: 10
    exact_match: no
    remove_duplicate: yes
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    # Extend the ZabbixAPI
    # Since the zabbix-api python module too old (version 1.0, no higher version so far),
    # it does not support the 'hostinterface' api calls,
    # so we have to inherit the ZabbixAPI class to add 'hostinterface' support.
    class ZabbixAPIExtends(ZabbixAPI):
        hostinterface = None

        def __init__(self, server, timeout, user, passwd, **kwargs):
            ZabbixAPI.__init__(self, server, timeout=timeout, user=user, passwd=passwd)
            self.hostinterface = ZabbixAPISubClass(self, dict({"prefix": "hostinterface"}, **kwargs))

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


class Host(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def is_host_exist(self, host_name, exact_match):
        """ Check host exists """
        search_key = 'search'
        if exact_match:
            search_key = 'filter'
        result = self._zapi.host.get({search_key: {'host': host_name}})
        return result

    def get_hosts_by_host_name(self, host_name, exact_match):
        """ Get host by host name """
        search_key = 'search'
        if exact_match:
            search_key = 'filter'
        host_list = self._zapi.host.get({'output': 'extend', search_key: {'host': [host_name]}})
        if len(host_list) < 1:
            self._module.fail_json(msg="Host not found: %s" % host_name)
        else:
            return host_list

    def get_hosts_by_ip(self, host_ips):
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
                'hostids': hostinterface['hostid']
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
                self._zapi.host.delete([zabbix_host['hostid']])
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
            timeout=dict(type='int', default=10),
            exact_match=dict(type='bool', required=False, default=False),
            remove_duplicate=dict(type='bool', required=False, default=True)
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
    host_name = module.params['host_name']
    host_ips = module.params['host_ip']
    timeout = module.params['timeout']
    exact_match = module.params['exact_match']
    is_remove_duplicate = module.params['remove_duplicate']

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPIExtends(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    host = Host(module, zbx)

    if host_name:
        is_host_exist = host.is_host_exist(host_name, exact_match)

        if is_host_exist:
            hosts = host.get_hosts_by_host_name(host_name, exact_match)
            if is_remove_duplicate:
                hosts = host.delete_duplicate_hosts(hosts)
            extended_hosts = []
            for zabbix_host in hosts:
                zabbix_host['hostinterfaces'] = host._zapi.hostinterface.get({
                    'output': 'extend', 'hostids': zabbix_host['hostid']
                })
                extended_hosts.append(zabbix_host)
            module.exit_json(ok=True, hosts=extended_hosts)
        else:
            module.exit_json(ok=False, hosts=[], result="No Host present")
    elif host_ips:
        extended_hosts = host.get_hosts_by_ip(host_ips)
        if is_remove_duplicate:
            hosts = host.delete_duplicate_hosts(extended_hosts)
        module.exit_json(ok=True, hosts=extended_hosts)
    else:
        module.exit_json(ok=False, hosts=[], result="No Host present")

if __name__ == '__main__':
    main()
