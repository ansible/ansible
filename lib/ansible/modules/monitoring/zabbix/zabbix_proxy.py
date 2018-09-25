#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2017, Alen Komic
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: zabbix_proxy
short_description: Zabbix proxy creates/deletes/gets/updates
description:
   - This module allows you to create, modify, get and delete Zabbix proxy entries.
version_added: "2.5"
author:
    - "Alen Komic"
requirements:
    - "python >= 2.6"
    - "zabbix-api >= 0.5.3"
options:
    proxy_name:
        description:
            - Name of the proxy in Zabbix.
        required: true
    description:
        description:
            - Description of the proxy..
        required: false
    status:
        description:
            - Type of proxy. (4 - active, 5 - passive)
        required: false
        choices: ['active', 'passive']
        default: "active"
    tls_connect:
        description:
            - Connections to proxy.
        required: false
        choices: ['no_encryption','PSK','certificate']
        default: 'no_encryption'
    tls_accept:
        description:
            - Connections from proxy.
        required: false
        choices: ['no_encryption','PSK','certificate']
        default: 'no_encryption'
    tls_issuer:
        description:
            - Certificate issuer.
        required: false
    tls_subject:
        description:
            - Certificate subject.
        required: false
    tls_psk_identity:
        description:
            - PSK identity. Required if either I(tls_connect) or I(tls_accept) has PSK enabled.
        required: false
    tls_psk:
        description:
            - The preshared key, at least 32 hex digits. Required if either I(tls_connect) or I(tls_accept) has PSK enabled.
        required: false
    state:
        description:
            - State of the proxy.
            - On C(present), it will create if proxy does not exist or update the proxy if the associated data is different.
            - On C(absent) will remove a proxy if it exists.
        required: false
        choices: ['present', 'absent']
        default: "present"
    interface:
        description:
            - Dictionary with params for the interface when proxy is in passive mode
            - 'Available values are: dns, ip, main, port, type and useip.'
            - Please review the interface documentation for more information on the supported properties
            - U(https://www.zabbix.com/documentation/3.2/manual/api/reference/proxy/object#proxy_interface)
        required: false
        default: {}

extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
- name: Create a new proxy or update an existing proxies info
  local_action:
    module: zabbix_proxy
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    proxy_name: ExampleProxy
    description: ExampleProxy
    status: active
    state: present
    interface:
        type: 0
        main: 1
        useip: 1
        ip: 10.xx.xx.xx
        dns: ""
        port: 10050
'''

RETURN = ''' # '''


from ansible.module_utils.basic import AnsibleModule
try:
    from zabbix_api import ZabbixAPI

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


class Proxy(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx
        self.existing_data = None

    def proxy_exists(self, proxy_name):
        result = self._zapi.proxy.get({
            'output': 'extend', 'selectInterface': 'extend',
            'filter': {'host': proxy_name}})

        if len(result) > 0 and 'proxyid' in result[0]:
            self.existing_data = result[0]
            return result[0]['proxyid']
        else:
            return result

    def add_proxy(self, data):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)

            parameters = {}
            for item in data:
                if data[item]:
                    parameters[item] = data[item]

            proxy_ids_list = self._zapi.proxy.create(parameters)
            self._module.exit_json(changed=True,
                                   result="Successfully added proxy %s (%s)" %
                                          (data['host'], data['status']))
            if len(proxy_ids_list) >= 1:
                return proxy_ids_list['proxyids'][0]
        except Exception as e:
            self._module.fail_json(msg="Failed to create proxy %s: %s" %
                                   (data['host'], e))

    def delete_proxy(self, proxy_id, proxy_name):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            self._zapi.proxy.delete([proxy_id])
            self._module.exit_json(changed=True,
                                   result="Successfully deleted" +
                                          " proxy %s" % proxy_name)
        except Exception as e:
            self._module.fail_json(msg="Failed to delete proxy %s: %s" %
                                       (proxy_name, str(e)))

    def compile_interface_params(self, new_interface):
        old_interface = {}
        if 'interface' in self.existing_data and \
           len(self.existing_data['interface']) > 0:
            old_interface = self.existing_data['interface']

        final_interface = old_interface.copy()
        final_interface.update(new_interface)
        final_interface = dict((k, str(v)) for k, v in final_interface.items())

        if final_interface != old_interface:
            return final_interface
        else:
            return {}

    def update_proxy(self, proxy_id, data):
        try:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            parameters = {'proxyid': proxy_id}

            for item in data:
                if data[item] and item in self.existing_data and \
                   self.existing_data[item] != data[item]:
                    parameters[item] = data[item]

            if 'interface' in parameters:
                parameters.pop('interface')

            if 'interface' in data and data['status'] == '6':
                new_interface = self.compile_interface_params(data['interface'])
                if len(new_interface) > 0:
                    parameters['interface'] = new_interface

            if len(parameters) > 1:
                self._zapi.proxy.update(parameters)
                self._module.exit_json(
                    changed=True,
                    result="Successfully updated proxy %s (%s)" %
                           (data['host'], proxy_id)
                )
            else:
                self._module.exit_json(changed=False)
        except Exception as e:
            self._module.fail_json(msg="Failed to update proxy %s: %s" %
                                       (data['host'], e))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            proxy_name=dict(type='str', required=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False,
                                     default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            status=dict(default="active", choices=['active', 'passive']),
            state=dict(default="present", choices=['present', 'absent']),
            description=dict(type='str', required=False),
            tls_connect=dict(default='no_encryption',
                             choices=['no_encryption', 'PSK', 'certificate']),
            tls_accept=dict(default='no_encryption',
                            choices=['no_encryption', 'PSK', 'certificate']),
            tls_issuer=dict(type='str', required=False, default=None),
            tls_subject=dict(type='str', required=False, default=None),
            tls_psk_identity=dict(type='str', required=False, default=None),
            tls_psk=dict(type='str', required=False, default=None),
            timeout=dict(type='int', default=10),
            interface=dict(type='dict', required=False, default={})
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing requried zabbix-api module" +
                             " (check docs or install with:" +
                             " pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    proxy_name = module.params['proxy_name']
    description = module.params['description']
    status = module.params['status']
    tls_connect = module.params['tls_connect']
    tls_accept = module.params['tls_accept']
    tls_issuer = module.params['tls_issuer']
    tls_subject = module.params['tls_subject']
    tls_psk_identity = module.params['tls_psk_identity']
    tls_psk = module.params['tls_psk']
    state = module.params['state']
    timeout = module.params['timeout']
    interface = module.params['interface']

    # convert enabled to 0; disabled to 1
    status = 6 if status == "passive" else 5

    if tls_connect == 'certificate':
        tls_connect = 4
    elif tls_connect == 'PSK':
        tls_connect = 2
    else:
        tls_connect = 1

    if tls_accept == 'certificate':
        tls_accept = 4
    elif tls_accept == 'PSK':
        tls_accept = 2
    else:
        tls_accept = 1

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout,
                        user=http_login_user,
                        passwd=http_login_password,
                        validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    proxy = Proxy(module, zbx)

    # check if proxy already exists
    proxy_id = proxy.proxy_exists(proxy_name)

    if proxy_id:
        if state == "absent":
            # remove proxy
            proxy.delete_proxy(proxy_id, proxy_name)
        else:
            proxy.update_proxy(proxy_id, {
                'host': proxy_name,
                'description': description,
                'status': str(status),
                'tls_connect': str(tls_connect),
                'tls_accept': str(tls_accept),
                'tls_issuer': tls_issuer,
                'tls_subject': tls_subject,
                'tls_psk_identity': tls_psk_identity,
                'tls_psk': tls_psk,
                'interface': interface
            })
    else:
        if state == "absent":
            # the proxy is already deleted.
            module.exit_json(changed=False)

        proxy_id = proxy.add_proxy(data={
            'host': proxy_name,
            'description': description,
            'status': str(status),
            'tls_connect': str(tls_connect),
            'tls_accept': str(tls_accept),
            'tls_issuer': tls_issuer,
            'tls_subject': tls_subject,
            'tls_psk_identity': tls_psk_identity,
            'tls_psk': tls_psk,
            'interface': interface
        })


if __name__ == '__main__':
    main()
