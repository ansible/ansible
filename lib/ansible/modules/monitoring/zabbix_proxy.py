#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Amine Ben Asker <ben.asker.amine@gmail.com> , yurilz.com.
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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_proxy
short_description: Zabbix  proxys creates/deletes
description:
   - Create host proxys if they do not exist.
   - Delete existing host proxys if they exist.
version_added: "2.4"
author:
    - "Amine Ben Asker (@asker_amine)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    server_url:
        description:
            - Url of Zabbix server, with protocol (http or https).
              C(url) is an alias for C(server_url).
        required: true
        aliases: [ "url" ]
    login_user:
        description:
            - Zabbix user name.
        required: true
    login_password:
        description:
            - Zabbix user password.
        required: true
    http_login_user:
        description:
            - Basic Auth login
        required: false
        default: None
        version_added: "2.1"
    http_login_password:
        description:
            - Basic Auth password
        required: false
        default: None
        version_added: "2.1"
    state:
        description:
            - Create or delete proxy.
        required: false
        default: "present"
        choices: [ "present", "absent" ]
    timeout:
        description:
            - The timeout of API request(seconds).
        default: 10
    proxy_name:
        description:
            -  The proxy name. It must be the same name as in the Hostname parameter in the proxy configuration file.
        required: true
    proxy_mode:
        description:
            -  Select the proxy mode.
        required: true
        choices: [ "active", "passive" ]
    proxy_hosts:
        description:
            -  List of hosts to be monitored by the proxy.
        required: false

notes:
    - Note that without encrypted communications (sensitive) proxy configuration data
      may become available to parties having access to the Zabbix server trapper port
      when using an active proxy.
'''

EXAMPLES = '''
# Base create host proxys example
- name: Create host proxys
  local_action:
    module: zabbix_proxy
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    state: present
    proxy_name: ZBXPROXY01
    proxy_mode: active

    zabbix_proxy:
      server_url: http://10.30.71.87/zabbix
      login_user: Admin
      login_password: zabbix
      state: present
      proxy_name:
          - ZBXPROXY01
      proxy_mode: passive
      proxy_interfaces:
        - ip: 10.20.30.40
          dns: ""
          useip: 1
          port: 10051

'''

RETURN = '''
state:
    description: Facts about the current state of the object.
    returned: always
    type: dict
'''

try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass
    from zabbix_api import Already_Exists

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule

class Proxy(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    # create proxy if not exists
    def __createQuery(self, proxy_name, proxy_mode,proxy_hosts,proxy_interface):
        query = {'host': proxy_name }

        if proxy_mode == "active":
            query['status'] = 5
        else:
            query['status'] = 6
            query['interface'] = proxy_interface
        return query

    def create_proxy(self, proxy_names, proxy_mode, proxy_hosts,interfaces):
        try:
            proxy_add_list = []
            for proxy_name in proxy_names:
                result = self._zapi.proxy.get({'filter': {'host': proxy_name}})
                if not result:
                    try:
                        if self._module.check_mode:
                            self._module.exit_json(changed=True)
                        self._zapi.proxy.create(self.__createQuery(proxy_name, proxy_mode, proxy_hosts, interfaces))
                        proxy_add_list.append(proxy_name)
                    except Already_Exists:
                        return proxy_add_list
            return proxy_add_list

        except Exception as e:
            self._module.fail_json(msg="Failed to create proxy(ies): %s" % e)

    # delete proxy(ies)
    def delete_proxy(self, proxy_ids):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.proxy.delete(proxy_ids)
        except Exception as e:
            self._module.fail_json(msg="Failed to delete proxy(ies), Exception: %s" % e)

    # get proxy ids by name
    def get_proxy_ids(self, proxy_names):
        proxy_ids = []

        proxy_list = self._zapi.proxy.get({'output': 'extend', 'filter': {'host': proxy_names}})
        for proxy in proxy_list:
            proxy_id = proxy['proxyid']
            proxy_ids.append(proxy_id)
        return proxy_ids, proxy_list


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str',required=False, default=None),
            http_login_password=dict(type='str',required=False, default=None, no_log=True),
            proxy_name=dict(type='list', required=True, aliases=['proxy_names']),
            proxy_mode=dict(required=True,  choices=['active','passive']),
            proxy_hosts=dict(type='list', required=False, default=None),
            state=dict(default="present", choices=['present','absent']),
            proxy_interfaces=dict(type='list', required=False),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )


    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing requried zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    proxy_name = module.params['proxy_name']
    proxy_mode = module.params['proxy_mode']
    proxy_hosts = module.params['proxy_hosts']
    if module.params['proxy_interfaces'] is not None:
        proxy_interface = module.params['proxy_interfaces'][0]
    elif proxy_mode == "passive":
        module.fail_json(msg="Missing requried interface for passive proxy")
    else:
        proxy_interface = None
    state = module.params['state']
    timeout = module.params['timeout']

    zbx = None

    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    proxy = Proxy(module, zbx)

    proxy_ids = []
    proxy_list = []
    if proxy_name:
        proxy_ids, proxy_list = proxy.get_proxy_ids(proxy_name)

    if state == "absent":
        # delete host proxy_name
        if proxy_ids:
            delete_proxy_names = []
            proxy.delete_proxy(proxy_ids)
            for proxy in proxy_list:
                delete_proxy_names.append(proxy['name'])
            module.exit_json(changed=True,
                             result="Successfully deleted host proxy(s): %s." % ",".join(delete_proxy_names))
        else:
            module.exit_json(changed=False, result="No host proxy(s) to delete.")
    else:
        # create host proxy_name
        proxy_add_list = proxy.create_proxy(proxy_name, proxy_mode, proxy_hosts,proxy_interface)
        if len(proxy_add_list) > 0:
            module.exit_json(changed=True, result="Successfully created host proxy(s): %s" % proxy_add_list)
        else:
            module.exit_json(changed=False)

if __name__ == '__main__':
    main()
