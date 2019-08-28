#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_system_fortiguard
short_description: Configure FortiGuard services in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and fortiguard category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.9"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
        description:
            - FortiOS or FortiGate IP address.
        type: str
        required: false
    username:
        description:
            - FortiOS or FortiGate username.
        type: str
        required: false
    password:
        description:
            - FortiOS or FortiGate password.
        type: str
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        type: str
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS protocol.
        type: bool
        default: true
    ssl_verify:
        description:
            - Ensures FortiGate certificate must be verified by a proper CA.
        type: bool
        default: true
    system_fortiguard:
        description:
            - Configure FortiGuard services.
        default: null
        type: dict
        suboptions:
            antispam_cache:
                description:
                    - Enable/disable FortiGuard antispam request caching. Uses a small amount of memory but improves performance.
                type: str
                choices:
                    - enable
                    - disable
            antispam_cache_mpercent:
                description:
                    - Maximum percent of FortiGate memory the antispam cache is allowed to use (1 - 15%).
                type: int
            antispam_cache_ttl:
                description:
                    - Time-to-live for antispam cache entries in seconds (300 - 86400). Lower times reduce the cache size. Higher times may improve
                       performance since the cache will have more entries.
                type: int
            antispam_expiration:
                description:
                    - Expiration date of the FortiGuard antispam contract.
                type: int
            antispam_force_off:
                description:
                    - Enable/disable turning off the FortiGuard antispam service.
                type: str
                choices:
                    - enable
                    - disable
            antispam_license:
                description:
                    - Interval of time between license checks for the FortiGuard antispam contract.
                type: int
            antispam_timeout:
                description:
                    - Antispam query time out (1 - 30 sec).
                type: int
            auto_join_forticloud:
                description:
                    - Automatically connect to and login to FortiCloud.
                type: str
                choices:
                    - enable
                    - disable
            ddns_server_ip:
                description:
                    - IP address of the FortiDDNS server.
                type: str
            ddns_server_port:
                description:
                    - Port used to communicate with FortiDDNS servers.
                type: int
            load_balance_servers:
                description:
                    - Number of servers to alternate between as first FortiGuard option.
                type: int
            outbreak_prevention_cache:
                description:
                    - Enable/disable FortiGuard Virus Outbreak Prevention cache.
                type: str
                choices:
                    - enable
                    - disable
            outbreak_prevention_cache_mpercent:
                description:
                    - Maximum percent of memory FortiGuard Virus Outbreak Prevention cache can use (1 - 15%).
                type: int
            outbreak_prevention_cache_ttl:
                description:
                    - Time-to-live for FortiGuard Virus Outbreak Prevention cache entries (300 - 86400 sec).
                type: int
            outbreak_prevention_expiration:
                description:
                    - Expiration date of FortiGuard Virus Outbreak Prevention contract.
                type: int
            outbreak_prevention_force_off:
                description:
                    - Turn off FortiGuard Virus Outbreak Prevention service.
                type: str
                choices:
                    - enable
                    - disable
            outbreak_prevention_license:
                description:
                    - Interval of time between license checks for FortiGuard Virus Outbreak Prevention contract.
                type: int
            outbreak_prevention_timeout:
                description:
                    - FortiGuard Virus Outbreak Prevention time out (1 - 30 sec).
                type: int
            port:
                description:
                    - Port used to communicate with the FortiGuard servers.
                type: str
                choices:
                    - 53
                    - 8888
                    - 80
            sdns_server_ip:
                description:
                    - IP address of the FortiDNS server.
                type: str
            sdns_server_port:
                description:
                    - Port used to communicate with FortiDNS servers.
                type: int
            service_account_id:
                description:
                    - Service account ID.
                type: str
            source_ip:
                description:
                    - Source IPv4 address used to communicate with FortiGuard.
                type: str
            source_ip6:
                description:
                    - Source IPv6 address used to communicate with FortiGuard.
                type: str
            update_server_location:
                description:
                    - Signature update server location.
                type: str
                choices:
                    - usa
                    - any
            webfilter_cache:
                description:
                    - Enable/disable FortiGuard web filter caching.
                type: str
                choices:
                    - enable
                    - disable
            webfilter_cache_ttl:
                description:
                    - Time-to-live for web filter cache entries in seconds (300 - 86400).
                type: int
            webfilter_expiration:
                description:
                    - Expiration date of the FortiGuard web filter contract.
                type: int
            webfilter_force_off:
                description:
                    - Enable/disable turning off the FortiGuard web filtering service.
                type: str
                choices:
                    - enable
                    - disable
            webfilter_license:
                description:
                    - Interval of time between license checks for the FortiGuard web filter contract.
                type: int
            webfilter_timeout:
                description:
                    - Web filter query time out (1 - 30 sec).
                type: int
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
   ssl_verify: "False"
  tasks:
  - name: Configure FortiGuard services.
    fortios_system_fortiguard:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_fortiguard:
        antispam_cache: "enable"
        antispam_cache_mpercent: "4"
        antispam_cache_ttl: "5"
        antispam_expiration: "6"
        antispam_force_off: "enable"
        antispam_license: "8"
        antispam_timeout: "9"
        auto_join_forticloud: "enable"
        ddns_server_ip: "<your_own_value>"
        ddns_server_port: "12"
        load_balance_servers: "13"
        outbreak_prevention_cache: "enable"
        outbreak_prevention_cache_mpercent: "15"
        outbreak_prevention_cache_ttl: "16"
        outbreak_prevention_expiration: "17"
        outbreak_prevention_force_off: "enable"
        outbreak_prevention_license: "19"
        outbreak_prevention_timeout: "20"
        port: "53"
        sdns_server_ip: "<your_own_value>"
        sdns_server_port: "23"
        service_account_id: "<your_own_value>"
        source_ip: "84.230.14.43"
        source_ip6: "<your_own_value>"
        update_server_location: "usa"
        webfilter_cache: "enable"
        webfilter_cache_ttl: "29"
        webfilter_expiration: "30"
        webfilter_force_off: "enable"
        webfilter_license: "32"
        webfilter_timeout: "33"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.fortios.fortios import FortiOSHandler
from ansible.module_utils.network.fortimanager.common import FAIL_SOCKET_MSG


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']
    ssl_verify = data['ssl_verify']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password, verify=ssl_verify)


def filter_system_fortiguard_data(json):
    option_list = ['antispam_cache', 'antispam_cache_mpercent', 'antispam_cache_ttl',
                   'antispam_expiration', 'antispam_force_off', 'antispam_license',
                   'antispam_timeout', 'auto_join_forticloud', 'ddns_server_ip',
                   'ddns_server_port', 'load_balance_servers', 'outbreak_prevention_cache',
                   'outbreak_prevention_cache_mpercent', 'outbreak_prevention_cache_ttl', 'outbreak_prevention_expiration',
                   'outbreak_prevention_force_off', 'outbreak_prevention_license', 'outbreak_prevention_timeout',
                   'port', 'sdns_server_ip', 'sdns_server_port',
                   'service_account_id', 'source_ip', 'source_ip6',
                   'update_server_location', 'webfilter_cache', 'webfilter_cache_ttl',
                   'webfilter_expiration', 'webfilter_force_off', 'webfilter_license',
                   'webfilter_timeout']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def underscore_to_hyphen(data):
    if isinstance(data, list):
        for elem in data:
            elem = underscore_to_hyphen(elem)
    elif isinstance(data, dict):
        new_data = {}
        for k, v in data.items():
            new_data[k.replace('_', '-')] = underscore_to_hyphen(v)
        data = new_data

    return data


def system_fortiguard(data, fos):
    vdom = data['vdom']
    system_fortiguard_data = data['system_fortiguard']
    filtered_data = underscore_to_hyphen(filter_system_fortiguard_data(system_fortiguard_data))

    return fos.set('system',
                   'fortiguard',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_fortiguard']:
        resp = system_fortiguard(data, fos)

    return not is_successful_status(resp), \
        resp['status'] == "success", \
        resp


def main():
    fields = {
        "host": {"required": False, "type": "str"},
        "username": {"required": False, "type": "str"},
        "password": {"required": False, "type": "str", "default": "", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ssl_verify": {"required": False, "type": "bool", "default": True},
        "system_fortiguard": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "antispam_cache": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "antispam_cache_mpercent": {"required": False, "type": "int"},
                "antispam_cache_ttl": {"required": False, "type": "int"},
                "antispam_expiration": {"required": False, "type": "int"},
                "antispam_force_off": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "antispam_license": {"required": False, "type": "int"},
                "antispam_timeout": {"required": False, "type": "int"},
                "auto_join_forticloud": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "ddns_server_ip": {"required": False, "type": "str"},
                "ddns_server_port": {"required": False, "type": "int"},
                "load_balance_servers": {"required": False, "type": "int"},
                "outbreak_prevention_cache": {"required": False, "type": "str",
                                              "choices": ["enable", "disable"]},
                "outbreak_prevention_cache_mpercent": {"required": False, "type": "int"},
                "outbreak_prevention_cache_ttl": {"required": False, "type": "int"},
                "outbreak_prevention_expiration": {"required": False, "type": "int"},
                "outbreak_prevention_force_off": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "outbreak_prevention_license": {"required": False, "type": "int"},
                "outbreak_prevention_timeout": {"required": False, "type": "int"},
                "port": {"required": False, "type": "str",
                         "choices": ["53", "8888", "80"]},
                "sdns_server_ip": {"required": False, "type": "str"},
                "sdns_server_port": {"required": False, "type": "int"},
                "service_account_id": {"required": False, "type": "str"},
                "source_ip": {"required": False, "type": "str"},
                "source_ip6": {"required": False, "type": "str"},
                "update_server_location": {"required": False, "type": "str",
                                           "choices": ["usa", "any"]},
                "webfilter_cache": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "webfilter_cache_ttl": {"required": False, "type": "int"},
                "webfilter_expiration": {"required": False, "type": "int"},
                "webfilter_force_off": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "webfilter_license": {"required": False, "type": "int"},
                "webfilter_timeout": {"required": False, "type": "int"}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # legacy_mode refers to using fortiosapi instead of HTTPAPI
    legacy_mode = 'host' in module.params and module.params['host'] is not None and \
                  'username' in module.params and module.params['username'] is not None and \
                  'password' in module.params and module.params['password'] is not None

    if not legacy_mode:
        if module._socket_path:
            connection = Connection(module._socket_path)
            fos = FortiOSHandler(connection)

            is_error, has_changed, result = fortios_system(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_system(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
