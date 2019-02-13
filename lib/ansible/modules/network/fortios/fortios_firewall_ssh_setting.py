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
module: fortios_firewall_ssh_setting
short_description: SSH proxy settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall_ssh feature and setting category.
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
    firewall_ssh_setting:
        description:
            - SSH proxy settings.
        default: null
        suboptions:
            caname:
                description:
                    - CA certificate used by SSH Inspection. Source firewall.ssh.local-ca.name.
            host-trusted-checking:
                description:
                    - Enable/disable host trusted checking.
                choices:
                    - enable
                    - disable
            hostkey-dsa1024:
                description:
                    - DSA certificate used by SSH proxy. Source firewall.ssh.local-key.name.
            hostkey-ecdsa256:
                description:
                    - ECDSA nid256 certificate used by SSH proxy. Source firewall.ssh.local-key.name.
            hostkey-ecdsa384:
                description:
                    - ECDSA nid384 certificate used by SSH proxy. Source firewall.ssh.local-key.name.
            hostkey-ecdsa521:
                description:
                    - ECDSA nid384 certificate used by SSH proxy. Source firewall.ssh.local-key.name.
            hostkey-ed25519:
                description:
                    - ED25519 hostkey used by SSH proxy. Source firewall.ssh.local-key.name.
            hostkey-rsa2048:
                description:
                    - RSA certificate used by SSH proxy. Source firewall.ssh.local-key.name.
            untrusted-caname:
                description:
                    - Untrusted CA certificate used by SSH Inspection. Source firewall.ssh.local-ca.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: SSH proxy settings.
    fortios_firewall_ssh_setting:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_ssh_setting:
        caname: "<your_own_value> (source firewall.ssh.local-ca.name)"
        host-trusted-checking: "enable"
        hostkey-dsa1024: "myhostname (source firewall.ssh.local-key.name)"
        hostkey-ecdsa256: "myhostname (source firewall.ssh.local-key.name)"
        hostkey-ecdsa384: "myhostname (source firewall.ssh.local-key.name)"
        hostkey-ecdsa521: "myhostname (source firewall.ssh.local-key.name)"
        hostkey-ed25519: "myhostname (source firewall.ssh.local-key.name)"
        hostkey-rsa2048: "myhostname (source firewall.ssh.local-key.name)"
        untrusted-caname: "<your_own_value> (source firewall.ssh.local-ca.name)"
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


def filter_firewall_ssh_setting_data(json):
    option_list = ['caname', 'host-trusted-checking', 'hostkey-dsa1024',
                   'hostkey-ecdsa256', 'hostkey-ecdsa384', 'hostkey-ecdsa521',
                   'hostkey-ed25519', 'hostkey-rsa2048', 'untrusted-caname']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_ssh_setting(data, fos):
    vdom = data['vdom']
    firewall_ssh_setting_data = data['firewall_ssh_setting']
    filtered_data = filter_firewall_ssh_setting_data(firewall_ssh_setting_data)
    return fos.set('firewall.ssh',
                   'setting',
                   data=filtered_data,
                   vdom=vdom)


def fortios_firewall_ssh(data, fos):
    login(data)

    methodlist = ['firewall_ssh_setting']
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
        "firewall_ssh_setting": {
            "required": False, "type": "dict",
            "options": {
                "caname": {"required": False, "type": "str"},
                "host-trusted-checking": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "hostkey-dsa1024": {"required": False, "type": "str"},
                "hostkey-ecdsa256": {"required": False, "type": "str"},
                "hostkey-ecdsa384": {"required": False, "type": "str"},
                "hostkey-ecdsa521": {"required": False, "type": "str"},
                "hostkey-ed25519": {"required": False, "type": "str"},
                "hostkey-rsa2048": {"required": False, "type": "str"},
                "untrusted-caname": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_firewall_ssh(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
