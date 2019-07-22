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
module: fortios_wireless_controller_global
short_description: Configure wireless controller global settings in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify wireless_controller feature and global category.
      Examples include all parameters and values need to be adjusted to datasources before usage.
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
    wireless_controller_global:
        description:
            - Configure wireless controller global settings.
        default: null
        suboptions:
            ap-log-server:
                description:
                    - Enable/disable configuring APs or FortiAPs to send log messages to a syslog server (default = disable).
                choices:
                    - enable
                    - disable
            ap-log-server-ip:
                description:
                    - IP address that APs or FortiAPs send log messages to.
            ap-log-server-port:
                description:
                    - Port that APs or FortiAPs send log messages to.
            control-message-offload:
                description:
                    - Configure CAPWAP control message data channel offload.
                choices:
                    - ebp-frame
                    - aeroscout-tag
                    - ap-list
                    - sta-list
                    - sta-cap-list
                    - stats
                    - aeroscout-mu
            data-ethernet-II:
                description:
                    - Configure the wireless controller to use Ethernet II or 802.3 frames with 802.3 data tunnel mode (default = disable).
                choices:
                    - enable
                    - disable
            discovery-mc-addr:
                description:
                    - Multicast IP address for AP discovery (default = 244.0.1.140).
            fiapp-eth-type:
                description:
                    - Ethernet type for Fortinet Inter-Access Point Protocol (IAPP), or IEEE 802.11f, packets (0 - 65535, default = 5252).
            image-download:
                description:
                    - Enable/disable WTP image download at join time.
                choices:
                    - enable
                    - disable
            ipsec-base-ip:
                description:
                    - Base IP address for IPsec VPN tunnels between the access points and the wireless controller (default = 169.254.0.1).
            link-aggregation:
                description:
                    - Enable/disable calculating the CAPWAP transmit hash to load balance sessions to link aggregation nodes (default = disable).
                choices:
                    - enable
                    - disable
            location:
                description:
                    - Description of the location of the wireless controller.
            max-clients:
                description:
                    - Maximum number of clients that can connect simultaneously (default = 0, meaning no limitation).
            max-retransmit:
                description:
                    - Maximum number of tunnel packet retransmissions (0 - 64, default = 3).
            mesh-eth-type:
                description:
                    - Mesh Ethernet identifier included in backhaul packets (0 - 65535, default = 8755).
            name:
                description:
                    - Name of the wireless controller.
            rogue-scan-mac-adjacency:
                description:
                    - Maximum numerical difference between an AP's Ethernet and wireless MAC values to match for rogue detection (0 - 31, default = 7).
            wtp-share:
                description:
                    - Enable/disable sharing of WTPs between VDOMs.
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
  - name: Configure wireless controller global settings.
    fortios_wireless_controller_global:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wireless_controller_global:
        ap-log-server: "enable"
        ap-log-server-ip: "<your_own_value>"
        ap-log-server-port: "5"
        control-message-offload: "ebp-frame"
        data-ethernet-II: "enable"
        discovery-mc-addr: "<your_own_value>"
        fiapp-eth-type: "9"
        image-download: "enable"
        ipsec-base-ip: "<your_own_value>"
        link-aggregation: "enable"
        location: "<your_own_value>"
        max-clients: "14"
        max-retransmit: "15"
        mesh-eth-type: "16"
        name: "default_name_17"
        rogue-scan-mac-adjacency: "18"
        wtp-share: "enable"
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


def login(data, fos):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_wireless_controller_global_data(json):
    option_list = ['ap-log-server', 'ap-log-server-ip', 'ap-log-server-port',
                   'control-message-offload', 'data-ethernet-II', 'discovery-mc-addr',
                   'fiapp-eth-type', 'image-download', 'ipsec-base-ip',
                   'link-aggregation', 'location', 'max-clients',
                   'max-retransmit', 'mesh-eth-type', 'name',
                   'rogue-scan-mac-adjacency', 'wtp-share']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def wireless_controller_global(data, fos):
    vdom = data['vdom']
    wireless_controller_global_data = data['wireless_controller_global']
    filtered_data = filter_wireless_controller_global_data(wireless_controller_global_data)

    return fos.set('wireless-controller',
                   'global',
                   data=filtered_data,
                   vdom=vdom)


def fortios_wireless_controller(data, fos):
    login(data, fos)

    if data['wireless_controller_global']:
        resp = wireless_controller_global(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "wireless_controller_global": {
            "required": False, "type": "dict",
            "options": {
                "ap-log-server": {"required": False, "type": "str",
                                  "choices": ["enable", "disable"]},
                "ap-log-server-ip": {"required": False, "type": "str"},
                "ap-log-server-port": {"required": False, "type": "int"},
                "control-message-offload": {"required": False, "type": "str",
                                            "choices": ["ebp-frame", "aeroscout-tag", "ap-list",
                                                        "sta-list", "sta-cap-list", "stats",
                                                        "aeroscout-mu"]},
                "data-ethernet-II": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "discovery-mc-addr": {"required": False, "type": "ipv4-address-multicast"},
                "fiapp-eth-type": {"required": False, "type": "int"},
                "image-download": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ipsec-base-ip": {"required": False, "type": "str"},
                "link-aggregation": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "location": {"required": False, "type": "str"},
                "max-clients": {"required": False, "type": "int"},
                "max-retransmit": {"required": False, "type": "int"},
                "mesh-eth-type": {"required": False, "type": "int"},
                "name": {"required": False, "type": "str"},
                "rogue-scan-mac-adjacency": {"required": False, "type": "int"},
                "wtp-share": {"required": False, "type": "str",
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

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_wireless_controller(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
