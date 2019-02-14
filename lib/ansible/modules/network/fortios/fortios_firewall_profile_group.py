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
module: fortios_firewall_profile_group
short_description: Configure profile groups in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and profile_group category.
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
            - FortiOS or FortiGate ip address.
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
    firewall_profile_group:
        description:
            - Configure profile groups.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            application-list:
                description:
                    - Name of an existing Application list. Source application.list.name.
            av-profile:
                description:
                    - Name of an existing Antivirus profile. Source antivirus.profile.name.
            dlp-sensor:
                description:
                    - Name of an existing DLP sensor. Source dlp.sensor.name.
            dnsfilter-profile:
                description:
                    - Name of an existing DNS filter profile. Source dnsfilter.profile.name.
            icap-profile:
                description:
                    - Name of an existing ICAP profile. Source icap.profile.name.
            ips-sensor:
                description:
                    - Name of an existing IPS sensor. Source ips.sensor.name.
            name:
                description:
                    - Profile group name.
                required: true
            profile-protocol-options:
                description:
                    - Name of an existing Protocol options profile. Source firewall.profile-protocol-options.name.
            spamfilter-profile:
                description:
                    - Name of an existing Spam filter profile. Source spamfilter.profile.name.
            ssh-filter-profile:
                description:
                    - Name of an existing SSH filter profile. Source ssh-filter.profile.name.
            ssl-ssh-profile:
                description:
                    - Name of an existing SSL SSH profile. Source firewall.ssl-ssh-profile.name.
            voip-profile:
                description:
                    - Name of an existing VoIP profile. Source voip.profile.name.
            waf-profile:
                description:
                    - Name of an existing Web application firewall profile. Source waf.profile.name.
            webfilter-profile:
                description:
                    - Name of an existing Web filter profile. Source webfilter.profile.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure profile groups.
    fortios_firewall_profile_group:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      firewall_profile_group:
        state: "present"
        application-list: "<your_own_value> (source application.list.name)"
        av-profile: "<your_own_value> (source antivirus.profile.name)"
        dlp-sensor: "<your_own_value> (source dlp.sensor.name)"
        dnsfilter-profile: "<your_own_value> (source dnsfilter.profile.name)"
        icap-profile: "<your_own_value> (source icap.profile.name)"
        ips-sensor: "<your_own_value> (source ips.sensor.name)"
        name: "default_name_9"
        profile-protocol-options: "<your_own_value> (source firewall.profile-protocol-options.name)"
        spamfilter-profile: "<your_own_value> (source spamfilter.profile.name)"
        ssh-filter-profile: "<your_own_value> (source ssh-filter.profile.name)"
        ssl-ssh-profile: "<your_own_value> (source firewall.ssl-ssh-profile.name)"
        voip-profile: "<your_own_value> (source voip.profile.name)"
        waf-profile: "<your_own_value> (source waf.profile.name)"
        webfilter-profile: "<your_own_value> (source webfilter.profile.name)"
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


def filter_firewall_profile_group_data(json):
    option_list = ['application-list', 'av-profile', 'dlp-sensor',
                   'dnsfilter-profile', 'icap-profile', 'ips-sensor',
                   'name', 'profile-protocol-options', 'spamfilter-profile',
                   'ssh-filter-profile', 'ssl-ssh-profile', 'voip-profile',
                   'waf-profile', 'webfilter-profile']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_profile_group(data, fos):
    vdom = data['vdom']
    firewall_profile_group_data = data['firewall_profile_group']
    filtered_data = filter_firewall_profile_group_data(firewall_profile_group_data)
    if firewall_profile_group_data['state'] == "present":
        return fos.set('firewall',
                       'profile-group',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_profile_group_data['state'] == "absent":
        return fos.delete('firewall',
                          'profile-group',
                          mkey=filtered_data['name'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_profile_group']
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
        "firewall_profile_group": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "application-list": {"required": False, "type": "str"},
                "av-profile": {"required": False, "type": "str"},
                "dlp-sensor": {"required": False, "type": "str"},
                "dnsfilter-profile": {"required": False, "type": "str"},
                "icap-profile": {"required": False, "type": "str"},
                "ips-sensor": {"required": False, "type": "str"},
                "name": {"required": True, "type": "str"},
                "profile-protocol-options": {"required": False, "type": "str"},
                "spamfilter-profile": {"required": False, "type": "str"},
                "ssh-filter-profile": {"required": False, "type": "str"},
                "ssl-ssh-profile": {"required": False, "type": "str"},
                "voip-profile": {"required": False, "type": "str"},
                "waf-profile": {"required": False, "type": "str"},
                "webfilter-profile": {"required": False, "type": "str"}

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

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
