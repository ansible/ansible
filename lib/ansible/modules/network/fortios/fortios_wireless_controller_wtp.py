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
module: fortios_wireless_controller_wtp
short_description: Configure Wireless Termination Points (WTPs), that is, FortiAPs or APs to be managed by FortiGate in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify wireless_controller feature and wtp category.
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
    wireless_controller_wtp:
        description:
            - Configure Wireless Termination Points (WTPs), that is, FortiAPs or APs to be managed by FortiGate.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            admin:
                description:
                    - Configure how the FortiGate operating as a wireless controller discovers and manages this WTP, AP or FortiAP.
                choices:
                    - discovered
                    - disable
                    - enable
            allowaccess:
                description:
                    - Control management access to the managed WTP, FortiAP, or AP. Separate entries with a space.
                choices:
                    - telnet
                    - http
                    - https
                    - ssh
            bonjour-profile:
                description:
                    - Bonjour profile name. Source wireless-controller.bonjour-profile.name.
            coordinate-enable:
                description:
                    - Enable/disable WTP coordinates (X,Y axis).
                choices:
                    - enable
                    - disable
            coordinate-latitude:
                description:
                    - WTP latitude coordinate.
            coordinate-longitude:
                description:
                    - WTP longitude coordinate.
            coordinate-x:
                description:
                    - X axis coordinate.
            coordinate-y:
                description:
                    - Y axis coordinate.
            image-download:
                description:
                    - Enable/disable WTP image download.
                choices:
                    - enable
                    - disable
            index:
                description:
                    - Index (0 - 4294967295).
            ip-fragment-preventing:
                description:
                    - Method by which IP fragmentation is prevented for CAPWAP tunneled control and data packets (default = tcp-mss-adjust).
                choices:
                    - tcp-mss-adjust
                    - icmp-unreachable
            lan:
                description:
                    - WTP LAN port mapping.
                suboptions:
                    port-mode:
                        description:
                            - LAN port mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port-ssid:
                        description:
                            - Bridge LAN port to SSID. Source wireless-controller.vap.name.
                    port1-mode:
                        description:
                            - LAN port 1 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port1-ssid:
                        description:
                            - Bridge LAN port 1 to SSID. Source wireless-controller.vap.name.
                    port2-mode:
                        description:
                            - LAN port 2 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port2-ssid:
                        description:
                            - Bridge LAN port 2 to SSID. Source wireless-controller.vap.name.
                    port3-mode:
                        description:
                            - LAN port 3 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port3-ssid:
                        description:
                            - Bridge LAN port 3 to SSID. Source wireless-controller.vap.name.
                    port4-mode:
                        description:
                            - LAN port 4 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port4-ssid:
                        description:
                            - Bridge LAN port 4 to SSID. Source wireless-controller.vap.name.
                    port5-mode:
                        description:
                            - LAN port 5 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port5-ssid:
                        description:
                            - Bridge LAN port 5 to SSID. Source wireless-controller.vap.name.
                    port6-mode:
                        description:
                            - LAN port 6 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port6-ssid:
                        description:
                            - Bridge LAN port 6 to SSID. Source wireless-controller.vap.name.
                    port7-mode:
                        description:
                            - LAN port 7 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port7-ssid:
                        description:
                            - Bridge LAN port 7 to SSID. Source wireless-controller.vap.name.
                    port8-mode:
                        description:
                            - LAN port 8 mode.
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port8-ssid:
                        description:
                            - Bridge LAN port 8 to SSID. Source wireless-controller.vap.name.
            led-state:
                description:
                    - Enable to allow the FortiAPs LEDs to light. Disable to keep the LEDs off. You may want to keep the LEDs off so they are not distracting
                       in low light areas etc.
                choices:
                    - enable
                    - disable
            location:
                description:
                    - Field for describing the physical location of the WTP, AP or FortiAP.
            login-passwd:
                description:
                    - Set the managed WTP, FortiAP, or AP's administrator password.
            login-passwd-change:
                description:
                    - Change or reset the administrator password of a managed WTP, FortiAP or AP (yes, default, or no, default = no).
                choices:
                    - yes
                    - default
                    - no
            mesh-bridge-enable:
                description:
                    - Enable/disable mesh Ethernet bridge when WTP is configured as a mesh branch/leaf AP.
                choices:
                    - default
                    - enable
                    - disable
            name:
                description:
                    - WTP, AP or FortiAP configuration name.
            override-allowaccess:
                description:
                    - Enable to override the WTP profile management access configuration.
                choices:
                    - enable
                    - disable
            override-ip-fragment:
                description:
                    - Enable/disable overriding the WTP profile IP fragment prevention setting.
                choices:
                    - enable
                    - disable
            override-lan:
                description:
                    - Enable to override the WTP profile LAN port setting.
                choices:
                    - enable
                    - disable
            override-led-state:
                description:
                    - Enable to override the profile LED state setting for this FortiAP. You must enable this option to use the led-state command to turn off
                       the FortiAP's LEDs.
                choices:
                    - enable
                    - disable
            override-login-passwd-change:
                description:
                    - Enable to override the WTP profile login-password (administrator password) setting.
                choices:
                    - enable
                    - disable
            override-split-tunnel:
                description:
                    - Enable/disable overriding the WTP profile split tunneling setting.
                choices:
                    - enable
                    - disable
            override-wan-port-mode:
                description:
                    - Enable/disable overriding the wan-port-mode in the WTP profile.
                choices:
                    - enable
                    - disable
            radio-1:
                description:
                    - Configuration options for radio 1.
                suboptions:
                    auto-power-high:
                        description:
                            - Automatic transmission power high limit in decibels (dB) of the measured power referenced to one milliwatt (mW), or dBm (10 - 17
                               dBm, default = 17).
                    auto-power-level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference (default = enable).
                        choices:
                            - enable
                            - disable
                    auto-power-low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                    band:
                        description:
                            - WiFi band that Radio 1 operates on.
                        choices:
                            - 802.11a
                            - 802.11b
                            - 802.11g
                            - 802.11n
                            - 802.11n-5G
                            - 802.11n,g-only
                            - 802.11g-only
                            - 802.11n-only
                            - 802.11n-5G-only
                            - 802.11ac
                            - 802.11ac,n-only
                            - 802.11ac-only
                    channel:
                        description:
                            - Selected list of wireless radio channels.
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                    override-analysis:
                        description:
                            - Enable to override the WTP profile spectrum analysis configuration.
                        choices:
                            - enable
                            - disable
                    override-band:
                        description:
                            - Enable to override the WTP profile band setting.
                        choices:
                            - enable
                            - disable
                    override-channel:
                        description:
                            - Enable to override WTP profile channel settings.
                        choices:
                            - enable
                            - disable
                    override-txpower:
                        description:
                            - Enable to override the WTP profile power level configuration.
                        choices:
                            - enable
                            - disable
                    override-vaps:
                        description:
                            - Enable to override WTP profile Virtual Access Point (VAP) settings.
                        choices:
                            - enable
                            - disable
                    power-level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100, default = 100).
                    radio-id:
                        description:
                            - radio-id
                    spectrum-analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        choices:
                            - enable
                            - disable
                    vap-all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) (default = enable).
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
            radio-2:
                description:
                    - Configuration options for radio 2.
                suboptions:
                    auto-power-high:
                        description:
                            - Automatic transmission power high limit in decibels (dB) of the measured power referenced to one milliwatt (mW), or dBm (10 - 17
                               dBm, default = 17).
                    auto-power-level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference (default = enable).
                        choices:
                            - enable
                            - disable
                    auto-power-low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                    band:
                        description:
                            - WiFi band that Radio 1 operates on.
                        choices:
                            - 802.11a
                            - 802.11b
                            - 802.11g
                            - 802.11n
                            - 802.11n-5G
                            - 802.11n,g-only
                            - 802.11g-only
                            - 802.11n-only
                            - 802.11n-5G-only
                            - 802.11ac
                            - 802.11ac,n-only
                            - 802.11ac-only
                    channel:
                        description:
                            - Selected list of wireless radio channels.
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                    override-analysis:
                        description:
                            - Enable to override the WTP profile spectrum analysis configuration.
                        choices:
                            - enable
                            - disable
                    override-band:
                        description:
                            - Enable to override the WTP profile band setting.
                        choices:
                            - enable
                            - disable
                    override-channel:
                        description:
                            - Enable to override WTP profile channel settings.
                        choices:
                            - enable
                            - disable
                    override-txpower:
                        description:
                            - Enable to override the WTP profile power level configuration.
                        choices:
                            - enable
                            - disable
                    override-vaps:
                        description:
                            - Enable to override WTP profile Virtual Access Point (VAP) settings.
                        choices:
                            - enable
                            - disable
                    power-level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100, default = 100).
                    radio-id:
                        description:
                            - radio-id
                    spectrum-analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        choices:
                            - enable
                            - disable
                    vap-all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) (default = enable).
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
            split-tunneling-acl:
                description:
                    - Split tunneling ACL filter list.
                suboptions:
                    dest-ip:
                        description:
                            - Destination IP and mask for the split-tunneling subnet.
                    id:
                        description:
                            - ID.
                        required: true
            split-tunneling-acl-local-ap-subnet:
                description:
                    - Enable/disable automatically adding local subnetwork of FortiAP to split-tunneling ACL (default = disable).
                choices:
                    - enable
                    - disable
            split-tunneling-acl-path:
                description:
                    - Split tunneling ACL path is local/tunnel.
                choices:
                    - tunnel
                    - local
            tun-mtu-downlink:
                description:
                    - Downlink tunnel MTU in octets. Set the value to either 0 (by default), 576, or 1500.
            tun-mtu-uplink:
                description:
                    - Uplink tunnel maximum transmission unit (MTU) in octets (eight-bit bytes). Set the value to either 0 (by default), 576, or 1500.
            wan-port-mode:
                description:
                    - Enable/disable using the FortiAP WAN port as a LAN port.
                choices:
                    - wan-lan
                    - wan-only
            wtp-id:
                description:
                    - WTP ID.
                required: true
            wtp-mode:
                description:
                    - WTP, AP, or FortiAP operating mode; normal (by default) or remote. A tunnel mode SSID can be assigned to an AP in normal mode but not
                       remote mode, while a local-bridge mode SSID can be assigned to an AP in either normal mode or remote mode.
                choices:
                    - normal
                    - remote
            wtp-profile:
                description:
                    - WTP profile name to apply to this WTP, AP or FortiAP. Source wireless-controller.wtp-profile.name.
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure Wireless Termination Points (WTPs), that is, FortiAPs or APs to be managed by FortiGate.
    fortios_wireless_controller_wtp:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      wireless_controller_wtp:
        state: "present"
        admin: "discovered"
        allowaccess: "telnet"
        bonjour-profile: "<your_own_value> (source wireless-controller.bonjour-profile.name)"
        coordinate-enable: "enable"
        coordinate-latitude: "<your_own_value>"
        coordinate-longitude: "<your_own_value>"
        coordinate-x: "<your_own_value>"
        coordinate-y: "<your_own_value>"
        image-download: "enable"
        index: "12"
        ip-fragment-preventing: "tcp-mss-adjust"
        lan:
            port-mode: "offline"
            port-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port1-mode: "offline"
            port1-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port2-mode: "offline"
            port2-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port3-mode: "offline"
            port3-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port4-mode: "offline"
            port4-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port5-mode: "offline"
            port5-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port6-mode: "offline"
            port6-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port7-mode: "offline"
            port7-ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port8-mode: "offline"
            port8-ssid: "<your_own_value> (source wireless-controller.vap.name)"
        led-state: "enable"
        location: "<your_own_value>"
        login-passwd: "<your_own_value>"
        login-passwd-change: "yes"
        mesh-bridge-enable: "default"
        name: "default_name_38"
        override-allowaccess: "enable"
        override-ip-fragment: "enable"
        override-lan: "enable"
        override-led-state: "enable"
        override-login-passwd-change: "enable"
        override-split-tunnel: "enable"
        override-wan-port-mode: "enable"
        radio-1:
            auto-power-high: "47"
            auto-power-level: "enable"
            auto-power-low: "49"
            band: "802.11a"
            channel:
             -
                chan: "<your_own_value>"
            override-analysis: "enable"
            override-band: "enable"
            override-channel: "enable"
            override-txpower: "enable"
            override-vaps: "enable"
            power-level: "58"
            radio-id: "59"
            spectrum-analysis: "enable"
            vap-all: "enable"
            vaps:
             -
                name: "default_name_63 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
        radio-2:
            auto-power-high: "65"
            auto-power-level: "enable"
            auto-power-low: "67"
            band: "802.11a"
            channel:
             -
                chan: "<your_own_value>"
            override-analysis: "enable"
            override-band: "enable"
            override-channel: "enable"
            override-txpower: "enable"
            override-vaps: "enable"
            power-level: "76"
            radio-id: "77"
            spectrum-analysis: "enable"
            vap-all: "enable"
            vaps:
             -
                name: "default_name_81 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
        split-tunneling-acl:
         -
            dest-ip: "<your_own_value>"
            id:  "84"
        split-tunneling-acl-local-ap-subnet: "enable"
        split-tunneling-acl-path: "tunnel"
        tun-mtu-downlink: "87"
        tun-mtu-uplink: "88"
        wan-port-mode: "wan-lan"
        wtp-id: "<your_own_value>"
        wtp-mode: "normal"
        wtp-profile: "<your_own_value> (source wireless-controller.wtp-profile.name)"
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


def filter_wireless_controller_wtp_data(json):
    option_list = ['admin', 'allowaccess', 'bonjour-profile',
                   'coordinate-enable', 'coordinate-latitude', 'coordinate-longitude',
                   'coordinate-x', 'coordinate-y', 'image-download',
                   'index', 'ip-fragment-preventing', 'lan',
                   'led-state', 'location', 'login-passwd',
                   'login-passwd-change', 'mesh-bridge-enable', 'name',
                   'override-allowaccess', 'override-ip-fragment', 'override-lan',
                   'override-led-state', 'override-login-passwd-change', 'override-split-tunnel',
                   'override-wan-port-mode', 'radio-1', 'radio-2',
                   'split-tunneling-acl', 'split-tunneling-acl-local-ap-subnet', 'split-tunneling-acl-path',
                   'tun-mtu-downlink', 'tun-mtu-uplink', 'wan-port-mode',
                   'wtp-id', 'wtp-mode', 'wtp-profile']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def flatten_multilists_attributes(data):
    multilist_attrs = []

    for attr in multilist_attrs:
        try:
            path = "data['" + "']['".join(elem for elem in attr) + "']"
            current_val = eval(path)
            flattened_val = ' '.join(elem for elem in current_val)
            exec(path + '= flattened_val')
        except BaseException:
            pass

    return data


def wireless_controller_wtp(data, fos):
    vdom = data['vdom']
    wireless_controller_wtp_data = data['wireless_controller_wtp']
    flattened_data = flatten_multilists_attributes(wireless_controller_wtp_data)
    filtered_data = filter_wireless_controller_wtp_data(flattened_data)
    if wireless_controller_wtp_data['state'] == "present":
        return fos.set('wireless-controller',
                       'wtp',
                       data=filtered_data,
                       vdom=vdom)

    elif wireless_controller_wtp_data['state'] == "absent":
        return fos.delete('wireless-controller',
                          'wtp',
                          mkey=filtered_data['wtp-id'],
                          vdom=vdom)


def fortios_wireless_controller(data, fos):
    login(data, fos)

    if data['wireless_controller_wtp']:
        resp = wireless_controller_wtp(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "wireless_controller_wtp": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "admin": {"required": False, "type": "str",
                          "choices": ["discovered", "disable", "enable"]},
                "allowaccess": {"required": False, "type": "str",
                                "choices": ["telnet", "http", "https",
                                            "ssh"]},
                "bonjour-profile": {"required": False, "type": "str"},
                "coordinate-enable": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "coordinate-latitude": {"required": False, "type": "str"},
                "coordinate-longitude": {"required": False, "type": "str"},
                "coordinate-x": {"required": False, "type": "str"},
                "coordinate-y": {"required": False, "type": "str"},
                "image-download": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "index": {"required": False, "type": "int"},
                "ip-fragment-preventing": {"required": False, "type": "str",
                                           "choices": ["tcp-mss-adjust", "icmp-unreachable"]},
                "lan": {"required": False, "type": "dict",
                        "options": {
                            "port-mode": {"required": False, "type": "str",
                                          "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                      "bridge-to-ssid"]},
                            "port-ssid": {"required": False, "type": "str"},
                            "port1-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port1-ssid": {"required": False, "type": "str"},
                            "port2-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port2-ssid": {"required": False, "type": "str"},
                            "port3-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port3-ssid": {"required": False, "type": "str"},
                            "port4-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port4-ssid": {"required": False, "type": "str"},
                            "port5-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port5-ssid": {"required": False, "type": "str"},
                            "port6-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port6-ssid": {"required": False, "type": "str"},
                            "port7-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port7-ssid": {"required": False, "type": "str"},
                            "port8-mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port8-ssid": {"required": False, "type": "str"}
                        }},
                "led-state": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "location": {"required": False, "type": "str"},
                "login-passwd": {"required": False, "type": "str"},
                "login-passwd-change": {"required": False, "type": "str",
                                        "choices": ["yes", "default", "no"]},
                "mesh-bridge-enable": {"required": False, "type": "str",
                                       "choices": ["default", "enable", "disable"]},
                "name": {"required": False, "type": "str"},
                "override-allowaccess": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "override-ip-fragment": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "override-lan": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "override-led-state": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "override-login-passwd-change": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "override-split-tunnel": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "override-wan-port-mode": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "radio-1": {"required": False, "type": "dict",
                            "options": {
                                "auto-power-high": {"required": False, "type": "int"},
                                "auto-power-level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto-power-low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11n,g-only",
                                                     "802.11g-only", "802.11n-only", "802.11n-5G-only",
                                                     "802.11ac", "802.11ac,n-only", "802.11ac-only"]},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "override-analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "override-band": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "override-channel": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override-txpower": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override-vaps": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "power-level": {"required": False, "type": "int"},
                                "radio-id": {"required": False, "type": "int"},
                                "spectrum-analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "vap-all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "radio-2": {"required": False, "type": "dict",
                            "options": {
                                "auto-power-high": {"required": False, "type": "int"},
                                "auto-power-level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto-power-low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11n,g-only",
                                                     "802.11g-only", "802.11n-only", "802.11n-5G-only",
                                                     "802.11ac", "802.11ac,n-only", "802.11ac-only"]},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "override-analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "override-band": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "override-channel": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override-txpower": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override-vaps": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "power-level": {"required": False, "type": "int"},
                                "radio-id": {"required": False, "type": "int"},
                                "spectrum-analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "vap-all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "split-tunneling-acl": {"required": False, "type": "list",
                                        "options": {
                                            "dest-ip": {"required": False, "type": "str"},
                                            "id": {"required": True, "type": "int"}
                                        }},
                "split-tunneling-acl-local-ap-subnet": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                "split-tunneling-acl-path": {"required": False, "type": "str",
                                             "choices": ["tunnel", "local"]},
                "tun-mtu-downlink": {"required": False, "type": "int"},
                "tun-mtu-uplink": {"required": False, "type": "int"},
                "wan-port-mode": {"required": False, "type": "str",
                                  "choices": ["wan-lan", "wan-only"]},
                "wtp-id": {"required": True, "type": "str"},
                "wtp-mode": {"required": False, "type": "str",
                             "choices": ["normal", "remote"]},
                "wtp-profile": {"required": False, "type": "str"}

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
