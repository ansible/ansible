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
module: fortios_ips_global
short_description: Configure IPS global parameter in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify ips feature and global category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
      Tested with FOS v6.0.5
version_added: "2.8"
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
        version_added: 2.9
    ips_global:
        description:
            - Configure IPS global parameter.
        default: null
        type: dict
        suboptions:
            anomaly_mode:
                description:
                    - Global blocking mode for rate-based anomalies.
                type: str
                choices:
                    - periodical
                    - continuous
            database:
                description:
                    - Regular or extended IPS database. Regular protects against the latest common and in-the-wild attacks. Extended includes protection from
                       legacy attacks.
                type: str
                choices:
                    - regular
                    - extended
            deep_app_insp_db_limit:
                description:
                    - Limit on number of entries in deep application inspection database (1 - 2147483647, 0 = use recommended setting)
                type: int
            deep_app_insp_timeout:
                description:
                    - Timeout for Deep application inspection (1 - 2147483647 sec., 0 = use recommended setting).
                type: int
            engine_count:
                description:
                    - Number of IPS engines running. If set to the default value of 0, FortiOS sets the number to optimize performance depending on the number
                       of CPU cores.
                type: int
            exclude_signatures:
                description:
                    - Excluded signatures.
                type: str
                choices:
                    - none
                    - industrial
            fail_open:
                description:
                    - Enable to allow traffic if the IPS process crashes. Default is disable and IPS traffic is blocked when the IPS process crashes.
                type: str
                choices:
                    - enable
                    - disable
            intelligent_mode:
                description:
                    - Enable/disable IPS adaptive scanning (intelligent mode). Intelligent mode optimizes the scanning method for the type of traffic.
                type: str
                choices:
                    - enable
                    - disable
            session_limit_mode:
                description:
                    - Method of counting concurrent sessions used by session limit anomalies. Choose between greater accuracy (accurate) or improved
                       performance (heuristics).
                type: str
                choices:
                    - accurate
                    - heuristic
            skype_client_public_ipaddr:
                description:
                    - Public IP addresses of your network that receive Skype sessions. Helps identify Skype sessions. Separate IP addresses with commas.
                type: str
            socket_size:
                description:
                    - IPS socket buffer size (0 - 256 MB). Default depends on available memory. Can be changed to tune performance.
                type: int
            sync_session_ttl:
                description:
                    - Enable/disable use of kernel session TTL for IPS sessions.
                type: str
                choices:
                    - enable
                    - disable
            traffic_submit:
                description:
                    - Enable/disable submitting attack data found by this FortiGate to FortiGuard.
                type: str
                choices:
                    - enable
                    - disable
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
  - name: Configure IPS global parameter.
    fortios_ips_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      ips_global:
        anomaly_mode: "periodical"
        database: "regular"
        deep_app_insp_db_limit: "5"
        deep_app_insp_timeout: "6"
        engine_count: "7"
        exclude_signatures: "none"
        fail_open: "enable"
        intelligent_mode: "enable"
        session_limit_mode: "accurate"
        skype_client_public_ipaddr: "<your_own_value>"
        socket_size: "13"
        sync_session_ttl: "enable"
        traffic_submit: "enable"
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


def filter_ips_global_data(json):
    option_list = ['anomaly_mode', 'database', 'deep_app_insp_db_limit',
                   'deep_app_insp_timeout', 'engine_count', 'exclude_signatures',
                   'fail_open', 'intelligent_mode', 'session_limit_mode',
                   'skype_client_public_ipaddr', 'socket_size', 'sync_session_ttl',
                   'traffic_submit']
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


def ips_global(data, fos):
    vdom = data['vdom']
    ips_global_data = data['ips_global']
    filtered_data = underscore_to_hyphen(filter_ips_global_data(ips_global_data))

    return fos.set('ips',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_ips(data, fos):

    if data['ips_global']:
        resp = ips_global(data, fos)

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
        "ips_global": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "anomaly_mode": {"required": False, "type": "str",
                                 "choices": ["periodical", "continuous"]},
                "database": {"required": False, "type": "str",
                             "choices": ["regular", "extended"]},
                "deep_app_insp_db_limit": {"required": False, "type": "int"},
                "deep_app_insp_timeout": {"required": False, "type": "int"},
                "engine_count": {"required": False, "type": "int"},
                "exclude_signatures": {"required": False, "type": "str",
                                       "choices": ["none", "industrial"]},
                "fail_open": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "intelligent_mode": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "session_limit_mode": {"required": False, "type": "str",
                                       "choices": ["accurate", "heuristic"]},
                "skype_client_public_ipaddr": {"required": False, "type": "str"},
                "socket_size": {"required": False, "type": "int"},
                "sync_session_ttl": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "traffic_submit": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]}

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

            is_error, has_changed, result = fortios_ips(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_ips(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
