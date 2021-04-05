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
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify wireless_controller feature and wtp category.
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
    state:
        description:
            - Indicates whether to create or remove the object.
              This attribute was present already in previous version in a deeper level.
              It has been moved out to this outer level.
        type: str
        required: false
        choices:
            - present
            - absent
        version_added: 2.9
    wireless_controller_wtp:
        description:
            - Configure Wireless Termination Points (WTPs), that is, FortiAPs or APs to be managed by FortiGate.
        default: null
        type: dict
        suboptions:
            state:
                description:
                    - B(Deprecated)
                    - Starting with Ansible 2.9 we recommend using the top-level 'state' parameter.
                    - HORIZONTALLINE
                    - Indicates whether to create or remove the object.
                type: str
                required: false
                choices:
                    - present
                    - absent
            admin:
                description:
                    - Configure how the FortiGate operating as a wireless controller discovers and manages this WTP, AP or FortiAP.
                type: str
                choices:
                    - discovered
                    - disable
                    - enable
            allowaccess:
                description:
                    - Control management access to the managed WTP, FortiAP, or AP. Separate entries with a space.
                type: str
                choices:
                    - telnet
                    - http
                    - https
                    - ssh
            bonjour_profile:
                description:
                    - Bonjour profile name. Source wireless-controller.bonjour-profile.name.
                type: str
            coordinate_enable:
                description:
                    - Enable/disable WTP coordinates (X,Y axis).
                type: str
                choices:
                    - enable
                    - disable
            coordinate_latitude:
                description:
                    - WTP latitude coordinate.
                type: str
            coordinate_longitude:
                description:
                    - WTP longitude coordinate.
                type: str
            coordinate_x:
                description:
                    - X axis coordinate.
                type: str
            coordinate_y:
                description:
                    - Y axis coordinate.
                type: str
            image_download:
                description:
                    - Enable/disable WTP image download.
                type: str
                choices:
                    - enable
                    - disable
            index:
                description:
                    - Index (0 - 4294967295).
                type: int
            ip_fragment_preventing:
                description:
                    - Method by which IP fragmentation is prevented for CAPWAP tunneled control and data packets .
                type: str
                choices:
                    - tcp-mss-adjust
                    - icmp-unreachable
            lan:
                description:
                    - WTP LAN port mapping.
                type: dict
                suboptions:
                    port_mode:
                        description:
                            - LAN port mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port_ssid:
                        description:
                            - Bridge LAN port to SSID. Source wireless-controller.vap.name.
                        type: str
                    port1_mode:
                        description:
                            - LAN port 1 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port1_ssid:
                        description:
                            - Bridge LAN port 1 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port2_mode:
                        description:
                            - LAN port 2 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port2_ssid:
                        description:
                            - Bridge LAN port 2 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port3_mode:
                        description:
                            - LAN port 3 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port3_ssid:
                        description:
                            - Bridge LAN port 3 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port4_mode:
                        description:
                            - LAN port 4 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port4_ssid:
                        description:
                            - Bridge LAN port 4 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port5_mode:
                        description:
                            - LAN port 5 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port5_ssid:
                        description:
                            - Bridge LAN port 5 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port6_mode:
                        description:
                            - LAN port 6 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port6_ssid:
                        description:
                            - Bridge LAN port 6 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port7_mode:
                        description:
                            - LAN port 7 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port7_ssid:
                        description:
                            - Bridge LAN port 7 to SSID. Source wireless-controller.vap.name.
                        type: str
                    port8_mode:
                        description:
                            - LAN port 8 mode.
                        type: str
                        choices:
                            - offline
                            - nat-to-wan
                            - bridge-to-wan
                            - bridge-to-ssid
                    port8_ssid:
                        description:
                            - Bridge LAN port 8 to SSID. Source wireless-controller.vap.name.
                        type: str
            led_state:
                description:
                    - Enable to allow the FortiAPs LEDs to light. Disable to keep the LEDs off. You may want to keep the LEDs off so they are not distracting
                       in low light areas etc.
                type: str
                choices:
                    - enable
                    - disable
            location:
                description:
                    - Field for describing the physical location of the WTP, AP or FortiAP.
                type: str
            login_passwd:
                description:
                    - Set the managed WTP, FortiAP, or AP's administrator password.
                type: str
            login_passwd_change:
                description:
                    - Change or reset the administrator password of a managed WTP, FortiAP or AP (yes, default, or no).
                type: str
                choices:
                    - yes
                    - default
                    - no
            mesh_bridge_enable:
                description:
                    - Enable/disable mesh Ethernet bridge when WTP is configured as a mesh branch/leaf AP.
                type: str
                choices:
                    - default
                    - enable
                    - disable
            name:
                description:
                    - WTP, AP or FortiAP configuration name.
                type: str
            override_allowaccess:
                description:
                    - Enable to override the WTP profile management access configuration.
                type: str
                choices:
                    - enable
                    - disable
            override_ip_fragment:
                description:
                    - Enable/disable overriding the WTP profile IP fragment prevention setting.
                type: str
                choices:
                    - enable
                    - disable
            override_lan:
                description:
                    - Enable to override the WTP profile LAN port setting.
                type: str
                choices:
                    - enable
                    - disable
            override_led_state:
                description:
                    - Enable to override the profile LED state setting for this FortiAP. You must enable this option to use the led-state command to turn off
                       the FortiAP's LEDs.
                type: str
                choices:
                    - enable
                    - disable
            override_login_passwd_change:
                description:
                    - Enable to override the WTP profile login-password (administrator password) setting.
                type: str
                choices:
                    - enable
                    - disable
            override_split_tunnel:
                description:
                    - Enable/disable overriding the WTP profile split tunneling setting.
                type: str
                choices:
                    - enable
                    - disable
            override_wan_port_mode:
                description:
                    - Enable/disable overriding the wan-port-mode in the WTP profile.
                type: str
                choices:
                    - enable
                    - disable
            radio_1:
                description:
                    - Configuration options for radio 1.
                type: dict
                suboptions:
                    auto_power_high:
                        description:
                            - Automatic transmission power high limit in decibels (dB) of the measured power referenced to one milliwatt (mW), or dBm (10 - 17
                               dBm).
                        type: int
                    auto_power_level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference .
                        type: str
                        choices:
                            - enable
                            - disable
                    auto_power_low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                        type: int
                    band:
                        description:
                            - WiFi band that Radio 1 operates on.
                        type: str
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
                        type: list
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                                type: str
                    override_analysis:
                        description:
                            - Enable to override the WTP profile spectrum analysis configuration.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_band:
                        description:
                            - Enable to override the WTP profile band setting.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_channel:
                        description:
                            - Enable to override WTP profile channel settings.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_txpower:
                        description:
                            - Enable to override the WTP profile power level configuration.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_vaps:
                        description:
                            - Enable to override WTP profile Virtual Access Point (VAP) settings.
                        type: str
                        choices:
                            - enable
                            - disable
                    power_level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100).
                        type: int
                    radio_id:
                        description:
                            - radio-id
                        type: int
                    spectrum_analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        type: str
                        choices:
                            - enable
                            - disable
                    vap_all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) .
                        type: str
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
                                type: str
            radio_2:
                description:
                    - Configuration options for radio 2.
                type: dict
                suboptions:
                    auto_power_high:
                        description:
                            - Automatic transmission power high limit in decibels (dB) of the measured power referenced to one milliwatt (mW), or dBm (10 - 17
                               dBm).
                        type: int
                    auto_power_level:
                        description:
                            - Enable/disable automatic power-level adjustment to prevent co-channel interference .
                        type: str
                        choices:
                            - enable
                            - disable
                    auto_power_low:
                        description:
                            - Automatic transmission power low limit in dBm (the actual range of transmit power depends on the AP platform type).
                        type: int
                    band:
                        description:
                            - WiFi band that Radio 1 operates on.
                        type: str
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
                        type: list
                        suboptions:
                            chan:
                                description:
                                    - Channel number.
                                required: true
                                type: str
                    override_analysis:
                        description:
                            - Enable to override the WTP profile spectrum analysis configuration.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_band:
                        description:
                            - Enable to override the WTP profile band setting.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_channel:
                        description:
                            - Enable to override WTP profile channel settings.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_txpower:
                        description:
                            - Enable to override the WTP profile power level configuration.
                        type: str
                        choices:
                            - enable
                            - disable
                    override_vaps:
                        description:
                            - Enable to override WTP profile Virtual Access Point (VAP) settings.
                        type: str
                        choices:
                            - enable
                            - disable
                    power_level:
                        description:
                            - Radio power level as a percentage of the maximum transmit power (0 - 100).
                        type: int
                    radio_id:
                        description:
                            - radio-id
                        type: int
                    spectrum_analysis:
                        description:
                            - Enable/disable spectrum analysis to find interference that would negatively impact wireless performance.
                        type: str
                        choices:
                            - enable
                            - disable
                    vap_all:
                        description:
                            - Enable/disable the automatic inheritance of all Virtual Access Points (VAPs) .
                        type: str
                        choices:
                            - enable
                            - disable
                    vaps:
                        description:
                            - Manually selected list of Virtual Access Points (VAPs).
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Virtual Access Point (VAP) name. Source wireless-controller.vap-group.name wireless-controller.vap.name.
                                required: true
                                type: str
            split_tunneling_acl:
                description:
                    - Split tunneling ACL filter list.
                type: list
                suboptions:
                    dest_ip:
                        description:
                            - Destination IP and mask for the split-tunneling subnet.
                        type: str
                    id:
                        description:
                            - ID.
                        required: true
                        type: int
            split_tunneling_acl_local_ap_subnet:
                description:
                    - Enable/disable automatically adding local subnetwork of FortiAP to split-tunneling ACL .
                type: str
                choices:
                    - enable
                    - disable
            split_tunneling_acl_path:
                description:
                    - Split tunneling ACL path is local/tunnel.
                type: str
                choices:
                    - tunnel
                    - local
            tun_mtu_downlink:
                description:
                    - Downlink tunnel MTU in octets. Set the value to either 0 (by default), 576, or 1500.
                type: int
            tun_mtu_uplink:
                description:
                    - Uplink tunnel maximum transmission unit (MTU) in octets (eight-bit bytes). Set the value to either 0 (by default), 576, or 1500.
                type: int
            wan_port_mode:
                description:
                    - Enable/disable using the FortiAP WAN port as a LAN port.
                type: str
                choices:
                    - wan-lan
                    - wan-only
            wtp_id:
                description:
                    - WTP ID.
                type: str
            wtp_mode:
                description:
                    - WTP, AP, or FortiAP operating mode; normal (by default) or remote. A tunnel mode SSID can be assigned to an AP in normal mode but not
                       remote mode, while a local-bridge mode SSID can be assigned to an AP in either normal mode or remote mode.
                type: str
                choices:
                    - normal
                    - remote
            wtp_profile:
                description:
                    - WTP profile name to apply to this WTP, AP or FortiAP. Source wireless-controller.wtp-profile.name.
                type: str
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
  - name: Configure Wireless Termination Points (WTPs), that is, FortiAPs or APs to be managed by FortiGate.
    fortios_wireless_controller_wtp:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      state: "present"
      wireless_controller_wtp:
        admin: "discovered"
        allowaccess: "telnet"
        bonjour_profile: "<your_own_value> (source wireless-controller.bonjour-profile.name)"
        coordinate_enable: "enable"
        coordinate_latitude: "<your_own_value>"
        coordinate_longitude: "<your_own_value>"
        coordinate_x: "<your_own_value>"
        coordinate_y: "<your_own_value>"
        image_download: "enable"
        index: "12"
        ip_fragment_preventing: "tcp-mss-adjust"
        lan:
            port_mode: "offline"
            port_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port1_mode: "offline"
            port1_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port2_mode: "offline"
            port2_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port3_mode: "offline"
            port3_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port4_mode: "offline"
            port4_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port5_mode: "offline"
            port5_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port6_mode: "offline"
            port6_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port7_mode: "offline"
            port7_ssid: "<your_own_value> (source wireless-controller.vap.name)"
            port8_mode: "offline"
            port8_ssid: "<your_own_value> (source wireless-controller.vap.name)"
        led_state: "enable"
        location: "<your_own_value>"
        login_passwd: "<your_own_value>"
        login_passwd_change: "yes"
        mesh_bridge_enable: "default"
        name: "default_name_38"
        override_allowaccess: "enable"
        override_ip_fragment: "enable"
        override_lan: "enable"
        override_led_state: "enable"
        override_login_passwd_change: "enable"
        override_split_tunnel: "enable"
        override_wan_port_mode: "enable"
        radio_1:
            auto_power_high: "47"
            auto_power_level: "enable"
            auto_power_low: "49"
            band: "802.11a"
            channel:
             -
                chan: "<your_own_value>"
            override_analysis: "enable"
            override_band: "enable"
            override_channel: "enable"
            override_txpower: "enable"
            override_vaps: "enable"
            power_level: "58"
            radio_id: "59"
            spectrum_analysis: "enable"
            vap_all: "enable"
            vaps:
             -
                name: "default_name_63 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
        radio_2:
            auto_power_high: "65"
            auto_power_level: "enable"
            auto_power_low: "67"
            band: "802.11a"
            channel:
             -
                chan: "<your_own_value>"
            override_analysis: "enable"
            override_band: "enable"
            override_channel: "enable"
            override_txpower: "enable"
            override_vaps: "enable"
            power_level: "76"
            radio_id: "77"
            spectrum_analysis: "enable"
            vap_all: "enable"
            vaps:
             -
                name: "default_name_81 (source wireless-controller.vap-group.name wireless-controller.vap.name)"
        split_tunneling_acl:
         -
            dest_ip: "<your_own_value>"
            id:  "84"
        split_tunneling_acl_local_ap_subnet: "enable"
        split_tunneling_acl_path: "tunnel"
        tun_mtu_downlink: "87"
        tun_mtu_uplink: "88"
        wan_port_mode: "wan-lan"
        wtp_id: "<your_own_value>"
        wtp_mode: "normal"
        wtp_profile: "<your_own_value> (source wireless-controller.wtp-profile.name)"
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


def filter_wireless_controller_wtp_data(json):
    option_list = ['admin', 'allowaccess', 'bonjour_profile',
                   'coordinate_enable', 'coordinate_latitude', 'coordinate_longitude',
                   'coordinate_x', 'coordinate_y', 'image_download',
                   'index', 'ip_fragment_preventing', 'lan',
                   'led_state', 'location', 'login_passwd',
                   'login_passwd_change', 'mesh_bridge_enable', 'name',
                   'override_allowaccess', 'override_ip_fragment', 'override_lan',
                   'override_led_state', 'override_login_passwd_change', 'override_split_tunnel',
                   'override_wan_port_mode', 'radio_1', 'radio_2',
                   'split_tunneling_acl', 'split_tunneling_acl_local_ap_subnet', 'split_tunneling_acl_path',
                   'tun_mtu_downlink', 'tun_mtu_uplink', 'wan_port_mode',
                   'wtp_id', 'wtp_mode', 'wtp_profile']
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


def wireless_controller_wtp(data, fos):
    vdom = data['vdom']
    if 'state' in data and data['state']:
        state = data['state']
    elif 'state' in data['wireless_controller_wtp'] and data['wireless_controller_wtp']:
        state = data['wireless_controller_wtp']['state']
    else:
        state = True
    wireless_controller_wtp_data = data['wireless_controller_wtp']
    filtered_data = underscore_to_hyphen(filter_wireless_controller_wtp_data(wireless_controller_wtp_data))

    if state == "present":
        return fos.set('wireless-controller',
                       'wtp',
                       data=filtered_data,
                       vdom=vdom)

    elif state == "absent":
        return fos.delete('wireless-controller',
                          'wtp',
                          mkey=filtered_data['wtp-id'],
                          vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_wireless_controller(data, fos):

    if data['wireless_controller_wtp']:
        resp = wireless_controller_wtp(data, fos)

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
        "state": {"required": False, "type": "str",
                  "choices": ["present", "absent"]},
        "wireless_controller_wtp": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "state": {"required": False, "type": "str",
                          "choices": ["present", "absent"]},
                "admin": {"required": False, "type": "str",
                          "choices": ["discovered", "disable", "enable"]},
                "allowaccess": {"required": False, "type": "str",
                                "choices": ["telnet", "http", "https",
                                            "ssh"]},
                "bonjour_profile": {"required": False, "type": "str"},
                "coordinate_enable": {"required": False, "type": "str",
                                      "choices": ["enable", "disable"]},
                "coordinate_latitude": {"required": False, "type": "str"},
                "coordinate_longitude": {"required": False, "type": "str"},
                "coordinate_x": {"required": False, "type": "str"},
                "coordinate_y": {"required": False, "type": "str"},
                "image_download": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "index": {"required": False, "type": "int"},
                "ip_fragment_preventing": {"required": False, "type": "str",
                                           "choices": ["tcp-mss-adjust", "icmp-unreachable"]},
                "lan": {"required": False, "type": "dict",
                        "options": {
                            "port_mode": {"required": False, "type": "str",
                                          "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                      "bridge-to-ssid"]},
                            "port_ssid": {"required": False, "type": "str"},
                            "port1_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port1_ssid": {"required": False, "type": "str"},
                            "port2_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port2_ssid": {"required": False, "type": "str"},
                            "port3_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port3_ssid": {"required": False, "type": "str"},
                            "port4_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port4_ssid": {"required": False, "type": "str"},
                            "port5_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port5_ssid": {"required": False, "type": "str"},
                            "port6_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port6_ssid": {"required": False, "type": "str"},
                            "port7_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port7_ssid": {"required": False, "type": "str"},
                            "port8_mode": {"required": False, "type": "str",
                                           "choices": ["offline", "nat-to-wan", "bridge-to-wan",
                                                       "bridge-to-ssid"]},
                            "port8_ssid": {"required": False, "type": "str"}
                        }},
                "led_state": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "location": {"required": False, "type": "str"},
                "login_passwd": {"required": False, "type": "str", "no_log": True},
                "login_passwd_change": {"required": False, "type": "str",
                                        "choices": ["yes", "default", "no"]},
                "mesh_bridge_enable": {"required": False, "type": "str",
                                       "choices": ["default", "enable", "disable"]},
                "name": {"required": False, "type": "str"},
                "override_allowaccess": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "override_ip_fragment": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "override_lan": {"required": False, "type": "str",
                                 "choices": ["enable", "disable"]},
                "override_led_state": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "override_login_passwd_change": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "override_split_tunnel": {"required": False, "type": "str",
                                          "choices": ["enable", "disable"]},
                "override_wan_port_mode": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "radio_1": {"required": False, "type": "dict",
                            "options": {
                                "auto_power_high": {"required": False, "type": "int"},
                                "auto_power_level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto_power_low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11n,g-only",
                                                     "802.11g-only", "802.11n-only", "802.11n-5G-only",
                                                     "802.11ac", "802.11ac,n-only", "802.11ac-only"]},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "override_analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "override_band": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "override_channel": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override_txpower": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override_vaps": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "power_level": {"required": False, "type": "int"},
                                "radio_id": {"required": False, "type": "int"},
                                "spectrum_analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "vap_all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "radio_2": {"required": False, "type": "dict",
                            "options": {
                                "auto_power_high": {"required": False, "type": "int"},
                                "auto_power_level": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "auto_power_low": {"required": False, "type": "int"},
                                "band": {"required": False, "type": "str",
                                         "choices": ["802.11a", "802.11b", "802.11g",
                                                     "802.11n", "802.11n-5G", "802.11n,g-only",
                                                     "802.11g-only", "802.11n-only", "802.11n-5G-only",
                                                     "802.11ac", "802.11ac,n-only", "802.11ac-only"]},
                                "channel": {"required": False, "type": "list",
                                            "options": {
                                                "chan": {"required": True, "type": "str"}
                                            }},
                                "override_analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "override_band": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "override_channel": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override_txpower": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "override_vaps": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                                "power_level": {"required": False, "type": "int"},
                                "radio_id": {"required": False, "type": "int"},
                                "spectrum_analysis": {"required": False, "type": "str",
                                                      "choices": ["enable", "disable"]},
                                "vap_all": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "vaps": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }}
                            }},
                "split_tunneling_acl": {"required": False, "type": "list",
                                        "options": {
                                            "dest_ip": {"required": False, "type": "str"},
                                            "id": {"required": True, "type": "int"}
                                        }},
                "split_tunneling_acl_local_ap_subnet": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                "split_tunneling_acl_path": {"required": False, "type": "str",
                                             "choices": ["tunnel", "local"]},
                "tun_mtu_downlink": {"required": False, "type": "int"},
                "tun_mtu_uplink": {"required": False, "type": "int"},
                "wan_port_mode": {"required": False, "type": "str",
                                  "choices": ["wan-lan", "wan-only"]},
                "wtp_id": {"required": False, "type": "str"},
                "wtp_mode": {"required": False, "type": "str",
                             "choices": ["normal", "remote"]},
                "wtp_profile": {"required": False, "type": "str"}

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

            is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        else:
            module.fail_json(**FAIL_SOCKET_MSG)
    else:
        try:
            from fortiosapi import FortiOSAPI
        except ImportError:
            module.fail_json(msg="fortiosapi module is required")

        fos = FortiOSAPI()

        login(module.params, fos)
        is_error, has_changed, result = fortios_wireless_controller(module.params, fos)
        fos.logout()

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
