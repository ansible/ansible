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
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_ips_global
short_description: Configure IPS global parameter in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure ips feature and global category.
      Examples includes all options and need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
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
            - FortiOS or FortiGate ip adress.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: true
    ips_global:
        description:
            - Configure IPS global parameter.
        default: null
        suboptions:
            anomaly-mode:
                description:
                    - Global blocking mode for rate-based anomalies.
                choices:
                    - periodical
                    - continuous
            database:
                description:
                    - Regular or extended IPS database. Regular protects against the latest common and in-the-wild attacks. Extended includes protection from
                       legacy attacks.
                choices:
                    - regular
                    - extended
            deep-app-insp-db-limit:
                description:
                    - Limit on number of entries in deep application inspection database (1 - 2147483647, 0 = use recommended setting)
            deep-app-insp-timeout:
                description:
                    - Timeout for Deep application inspection (1 - 2147483647 sec., 0 = use recommended setting).
            engine-count:
                description:
                    - Number of IPS engines running. If set to the default value of 0, FortiOS sets the number to optimize performance depending on the number
                       of CPU cores.
            exclude-signatures:
                description:
                    - Excluded signatures.
                choices:
                    - none
                    - industrial
            fail-open:
                description:
                    - Enable to allow traffic if the IPS process crashes. Default is disable and IPS traffic is blocked when the IPS process crashes.
                choices:
                    - enable
                    - disable
            intelligent-mode:
                description:
                    - Enable/disable IPS adaptive scanning (intelligent mode). Intelligent mode optimizes the scanning method for the type of traffic.
                choices:
                    - enable
                    - disable
            session-limit-mode:
                description:
                    - Method of counting concurrent sessions used by session limit anomalies. Choose between greater accuracy (accurate) or improved
                       performance (heuristics).
                choices:
                    - accurate
                    - heuristic
            skype-client-public-ipaddr:
                description:
                    - Public IP addresses of your network that receive Skype sessions. Helps identify Skype sessions. Separate IP addresses with commas.
            socket-size:
                description:
                    - IPS socket buffer size (0 - 256 MB). Default depends on available memory. Can be changed to tune performance.
            sync-session-ttl:
                description:
                    - Enable/disable use of kernel session TTL for IPS sessions.
                choices:
                    - enable
                    - disable
            traffic-submit:
                description:
                    - Enable/disable submitting attack data found by this FortiGate to FortiGuard.
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
  tasks:
  - name: Configure IPS global parameter.
    fortios_ips_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      ips_global:
        anomaly-mode: "periodical"
        database: "regular"
        deep-app-insp-db-limit: "5"
        deep-app-insp-timeout: "6"
        engine-count: "7"
        exclude-signatures: "none"
        fail-open: "enable"
        intelligent-mode: "enable"
        session-limit-mode: "accurate"
        skype-client-public-ipaddr: "<your_own_value>"
        socket-size: "13"
        sync-session-ttl: "enable"
        traffic-submit: "enable"
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

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_ips_global_data(json):
    option_list = ['anomaly-mode', 'database', 'deep-app-insp-db-limit',
                   'deep-app-insp-timeout', 'engine-count', 'exclude-signatures',
                   'fail-open', 'intelligent-mode', 'session-limit-mode',
                   'skype-client-public-ipaddr', 'socket-size', 'sync-session-ttl',
                   'traffic-submit']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def ips_global(data, fos):
    vdom = data['vdom']
    ips_global_data = data['ips_global']
    filtered_data = filter_ips_global_data(ips_global_data)
    return fos.set('ips',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def fortios_ips(data, fos):
    login(data)

    methodlist = ['ips_global']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "ips_global": {
            "required": False, "type": "dict",
            "options": {
                "anomaly-mode": {"required": False, "type": "str",
                                 "choices": ["periodical", "continuous"]},
                "database": {"required": False, "type": "str",
                             "choices": ["regular", "extended"]},
                "deep-app-insp-db-limit": {"required": False, "type": "int"},
                "deep-app-insp-timeout": {"required": False, "type": "int"},
                "engine-count": {"required": False, "type": "int"},
                "exclude-signatures": {"required": False, "type": "str",
                                       "choices": ["none", "industrial"]},
                "fail-open": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "intelligent-mode": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "session-limit-mode": {"required": False, "type": "str",
                                       "choices": ["accurate", "heuristic"]},
                "skype-client-public-ipaddr": {"required": False, "type": "str"},
                "socket-size": {"required": False, "type": "int"},
                "sync-session-ttl": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "traffic-submit": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_ips(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
