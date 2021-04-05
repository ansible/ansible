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
module: fortios_system_virtual_wan_link
short_description: Configure redundant internet connections using SD-WAN (formerly virtual WAN link) in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and virtual_wan_link category.
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
    system_virtual_wan_link:
        description:
            - Configure redundant internet connections using SD-WAN (formerly virtual WAN link).
        default: null
        type: dict
        suboptions:
            fail_alert_interfaces:
                description:
                    - Physical interfaces that will be alerted.
                type: list
                suboptions:
                    name:
                        description:
                            - Physical interface name. Source system.interface.name.
                        required: true
                        type: str
            fail_detect:
                description:
                    - Enable/disable SD-WAN Internet connection status checking (failure detection).
                type: str
                choices:
                    - enable
                    - disable
            health_check:
                description:
                    - SD-WAN status checking or health checking. Identify a server on the Internet and determine how SD-WAN verifies that the FortiGate can
                       communicate with it.
                type: list
                suboptions:
                    addr_mode:
                        description:
                            - Address mode (IPv4 or IPv6).
                        type: str
                        choices:
                            - ipv4
                            - ipv6
                    failtime:
                        description:
                            - Number of failures before server is considered lost (1 - 3600).
                        type: int
                    http_agent:
                        description:
                            - String in the http-agent field in the HTTP header.
                        type: str
                    http_get:
                        description:
                            - URL used to communicate with the server if the protocol if the protocol is HTTP.
                        type: str
                    http_match:
                        description:
                            - Response string expected from the server if the protocol is HTTP.
                        type: str
                    interval:
                        description:
                            - Status check interval, or the time between attempting to connect to the server (1 - 3600 sec).
                        type: int
                    members:
                        description:
                            - Member sequence number list.
                        type: list
                        suboptions:
                            seq_num:
                                description:
                                    - Member sequence number. Source system.virtual-wan-link.members.seq-num.
                                type: int
                    name:
                        description:
                            - Status check or health check name.
                        required: true
                        type: str
                    packet_size:
                        description:
                            - Packet size of a twamp test session,
                        type: int
                    password:
                        description:
                            - Twamp controller password in authentication mode
                        type: str
                    port:
                        description:
                            - Port number used to communicate with the server over the selected protocol.
                        type: int
                    protocol:
                        description:
                            - Protocol used to determine if the FortiGate can communicate with the server.
                        type: str
                        choices:
                            - ping
                            - tcp-echo
                            - udp-echo
                            - http
                            - twamp
                            - ping6
                    recoverytime:
                        description:
                            - Number of successful responses received before server is considered recovered (1 - 3600).
                        type: int
                    security_mode:
                        description:
                            - Twamp controller security mode.
                        type: str
                        choices:
                            - none
                            - authentication
                    server:
                        description:
                            - IP address or FQDN name of the server.
                        type: str
                    sla:
                        description:
                            - Service level agreement (SLA).
                        type: list
                        suboptions:
                            id:
                                description:
                                    - SLA ID.
                                required: true
                                type: int
                            jitter_threshold:
                                description:
                                    - Jitter for SLA to make decision in milliseconds. (0 - 10000000).
                                type: int
                            latency_threshold:
                                description:
                                    - Latency for SLA to make decision in milliseconds. (0 - 10000000).
                                type: int
                            link_cost_factor:
                                description:
                                    - Criteria on which to base link selection.
                                type: str
                                choices:
                                    - latency
                                    - jitter
                                    - packet-loss
                            packetloss_threshold:
                                description:
                                    - Packet loss for SLA to make decision in percentage. (0 - 100).
                                type: int
                    threshold_alert_jitter:
                        description:
                            - Alert threshold for jitter (ms).
                        type: int
                    threshold_alert_latency:
                        description:
                            - Alert threshold for latency (ms).
                        type: int
                    threshold_alert_packetloss:
                        description:
                            - Alert threshold for packet loss (percentage).
                        type: int
                    threshold_warning_jitter:
                        description:
                            - Warning threshold for jitter (ms).
                        type: int
                    threshold_warning_latency:
                        description:
                            - Warning threshold for latency (ms).
                        type: int
                    threshold_warning_packetloss:
                        description:
                            - Warning threshold for packet loss (percentage).
                        type: int
                    update_cascade_interface:
                        description:
                            - Enable/disable update cascade interface.
                        type: str
                        choices:
                            - enable
                            - disable
                    update_static_route:
                        description:
                            - Enable/disable updating the static route.
                        type: str
                        choices:
                            - enable
                            - disable
            load_balance_mode:
                description:
                    - Algorithm or mode to use for load balancing Internet traffic to SD-WAN members.
                type: str
                choices:
                    - source-ip-based
                    - weight-based
                    - usage-based
                    - source-dest-ip-based
                    - measured-volume-based
            members:
                description:
                    - Physical FortiGate interfaces added to the virtual-wan-link.
                type: list
                suboptions:
                    comment:
                        description:
                            - Comments.
                        type: str
                    gateway:
                        description:
                            - The default gateway for this interface. Usually the default gateway of the Internet service provider that this interface is
                               connected to.
                        type: str
                    gateway6:
                        description:
                            - IPv6 gateway.
                        type: str
                    ingress_spillover_threshold:
                        description:
                            - Ingress spillover threshold for this interface (0 - 16776000 kbit/s). When this traffic volume threshold is reached, new
                               sessions spill over to other interfaces in the SD-WAN.
                        type: int
                    interface:
                        description:
                            - Interface name. Source system.interface.name.
                        type: str
                    priority:
                        description:
                            - Priority of the interface (0 - 4294967295). Used for SD-WAN rules or priority rules.
                        type: int
                    seq_num:
                        description:
                            - Sequence number(1-255).
                        type: int
                    source:
                        description:
                            - Source IP address used in the health-check packet to the server.
                        type: str
                    source6:
                        description:
                            - Source IPv6 address used in the health-check packet to the server.
                        type: str
                    spillover_threshold:
                        description:
                            - Egress spillover threshold for this interface (0 - 16776000 kbit/s). When this traffic volume threshold is reached, new sessions
                               spill over to other interfaces in the SD-WAN.
                        type: int
                    status:
                        description:
                            - Enable/disable this interface in the SD-WAN.
                        type: str
                        choices:
                            - disable
                            - enable
                    volume_ratio:
                        description:
                            - Measured volume ratio (this value / sum of all values = percentage of link volume, 0 - 255).
                        type: int
                    weight:
                        description:
                            - Weight of this interface for weighted load balancing. (0 - 255) More traffic is directed to interfaces with higher weights.
                        type: int
            service:
                description:
                    - Create SD-WAN rules or priority rules (also called services) to control how sessions are distributed to physical interfaces in the
                       SD-WAN.
                type: list
                suboptions:
                    addr_mode:
                        description:
                            - Address mode (IPv4 or IPv6).
                        type: str
                        choices:
                            - ipv4
                            - ipv6
                    bandwidth_weight:
                        description:
                            - Coefficient of reciprocal of available bidirectional bandwidth in the formula of custom-profile-1.
                        type: int
                    default:
                        description:
                            - Enable/disable use of SD-WAN as default service.
                        type: str
                        choices:
                            - enable
                            - disable
                    dscp_forward:
                        description:
                            - Enable/disable forward traffic DSCP tag.
                        type: str
                        choices:
                            - enable
                            - disable
                    dscp_forward_tag:
                        description:
                            - Forward traffic DSCP tag.
                        type: str
                    dscp_reverse:
                        description:
                            - Enable/disable reverse traffic DSCP tag.
                        type: str
                        choices:
                            - enable
                            - disable
                    dscp_reverse_tag:
                        description:
                            - Reverse traffic DSCP tag.
                        type: str
                    dst:
                        description:
                            - Destination address name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address or address group name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                                type: str
                    dst_negate:
                        description:
                            - Enable/disable negation of destination address match.
                        type: str
                        choices:
                            - enable
                            - disable
                    dst6:
                        description:
                            - Destination address6 name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address6 or address6 group name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                                type: str
                    end_port:
                        description:
                            - End destination port number.
                        type: int
                    gateway:
                        description:
                            - Enable/disable SD-WAN service gateway.
                        type: str
                        choices:
                            - enable
                            - disable
                    groups:
                        description:
                            - User groups.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Group name. Source user.group.name.
                                required: true
                                type: str
                    health_check:
                        description:
                            - Health check. Source system.virtual-wan-link.health-check.name.
                        type: str
                    hold_down_time:
                        description:
                            - Waiting period in seconds when switching from the back-up member to the primary member (0 - 10000000).
                        type: int
                    id:
                        description:
                            - Priority rule ID (1 - 4000).
                        required: true
                        type: int
                    input_device:
                        description:
                            - Source interface name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Interface name. Source system.interface.name.
                                required: true
                                type: str
                    internet_service:
                        description:
                            - Enable/disable use of Internet service for application-based load balancing.
                        type: str
                        choices:
                            - enable
                            - disable
                    internet_service_ctrl:
                        description:
                            - Control-based Internet Service ID list.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Control-based Internet Service ID.
                                required: true
                                type: int
                    internet_service_ctrl_group:
                        description:
                            - Control-based Internet Service group list.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Control-based Internet Service group name. Source application.group.name.
                                required: true
                                type: str
                    internet_service_custom:
                        description:
                            - Custom Internet service name list.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Custom Internet service name. Source firewall.internet-service-custom.name.
                                required: true
                                type: str
                    internet_service_custom_group:
                        description:
                            - Custom Internet Service group list.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Custom Internet Service group name. Source firewall.internet-service-custom-group.name.
                                required: true
                                type: str
                    internet_service_group:
                        description:
                            - Internet Service group list.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Internet Service group name. Source firewall.internet-service-group.name.
                                required: true
                                type: str
                    internet_service_id:
                        description:
                            - Internet service ID list.
                        type: list
                        suboptions:
                            id:
                                description:
                                    - Internet service ID. Source firewall.internet-service.id.
                                required: true
                                type: int
                    jitter_weight:
                        description:
                            - Coefficient of jitter in the formula of custom-profile-1.
                        type: int
                    latency_weight:
                        description:
                            - Coefficient of latency in the formula of custom-profile-1.
                        type: int
                    link_cost_factor:
                        description:
                            - Link cost factor.
                        type: str
                        choices:
                            - latency
                            - jitter
                            - packet-loss
                            - inbandwidth
                            - outbandwidth
                            - bibandwidth
                            - custom-profile-1
                    link_cost_threshold:
                        description:
                            - Percentage threshold change of link cost values that will result in policy route regeneration (0 - 10000000).
                        type: int
                    member:
                        description:
                            - Member sequence number.
                        type: int
                    mode:
                        description:
                            - Control how the priority rule sets the priority of interfaces in the SD-WAN.
                        type: str
                        choices:
                            - auto
                            - manual
                            - priority
                            - sla
                    name:
                        description:
                            - Priority rule name.
                        type: str
                    packet_loss_weight:
                        description:
                            - Coefficient of packet-loss in the formula of custom-profile-1.
                        type: int
                    priority_members:
                        description:
                            - Member sequence number list.
                        type: list
                        suboptions:
                            seq_num:
                                description:
                                    - Member sequence number. Source system.virtual-wan-link.members.seq-num.
                                type: int
                    protocol:
                        description:
                            - Protocol number.
                        type: int
                    quality_link:
                        description:
                            - Quality grade.
                        type: int
                    route_tag:
                        description:
                            - IPv4 route map route-tag.
                        type: int
                    sla:
                        description:
                            - Service level agreement (SLA).
                        type: list
                        suboptions:
                            health_check:
                                description:
                                    - Virtual WAN Link health-check. Source system.virtual-wan-link.health-check.name.
                                type: str
                            id:
                                description:
                                    - SLA ID.
                                type: int
                    src:
                        description:
                            - Source address name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address or address group name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                                type: str
                    src_negate:
                        description:
                            - Enable/disable negation of source address match.
                        type: str
                        choices:
                            - enable
                            - disable
                    src6:
                        description:
                            - Source address6 name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - Address6 or address6 group name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                                type: str
                    start_port:
                        description:
                            - Start destination port number.
                        type: int
                    status:
                        description:
                            - Enable/disable SD-WAN service.
                        type: str
                        choices:
                            - enable
                            - disable
                    tos:
                        description:
                            - Type of service bit pattern.
                        type: str
                    tos_mask:
                        description:
                            - Type of service evaluated bits.
                        type: str
                    users:
                        description:
                            - User name.
                        type: list
                        suboptions:
                            name:
                                description:
                                    - User name. Source user.local.name.
                                required: true
                                type: str
            status:
                description:
                    - Enable/disable SD-WAN.
                type: str
                choices:
                    - disable
                    - enable
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
  - name: Configure redundant internet connections using SD-WAN (formerly virtual WAN link).
    fortios_system_virtual_wan_link:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_virtual_wan_link:
        fail_alert_interfaces:
         -
            name: "default_name_4 (source system.interface.name)"
        fail_detect: "enable"
        health_check:
         -
            addr_mode: "ipv4"
            failtime: "8"
            http_agent: "<your_own_value>"
            http_get: "<your_own_value>"
            http_match: "<your_own_value>"
            interval: "12"
            members:
             -
                seq_num: "14 (source system.virtual-wan-link.members.seq-num)"
            name: "default_name_15"
            packet_size: "16"
            password: "<your_own_value>"
            port: "18"
            protocol: "ping"
            recoverytime: "20"
            security_mode: "none"
            server: "192.168.100.40"
            sla:
             -
                id:  "24"
                jitter_threshold: "25"
                latency_threshold: "26"
                link_cost_factor: "latency"
                packetloss_threshold: "28"
            threshold_alert_jitter: "29"
            threshold_alert_latency: "30"
            threshold_alert_packetloss: "31"
            threshold_warning_jitter: "32"
            threshold_warning_latency: "33"
            threshold_warning_packetloss: "34"
            update_cascade_interface: "enable"
            update_static_route: "enable"
        load_balance_mode: "source-ip-based"
        members:
         -
            comment: "Comments."
            gateway: "<your_own_value>"
            gateway6: "<your_own_value>"
            ingress_spillover_threshold: "42"
            interface: "<your_own_value> (source system.interface.name)"
            priority: "44"
            seq_num: "45"
            source: "<your_own_value>"
            source6: "<your_own_value>"
            spillover_threshold: "48"
            status: "disable"
            volume_ratio: "50"
            weight: "51"
        service:
         -
            addr_mode: "ipv4"
            bandwidth_weight: "54"
            default: "enable"
            dscp_forward: "enable"
            dscp_forward_tag: "<your_own_value>"
            dscp_reverse: "enable"
            dscp_reverse_tag: "<your_own_value>"
            dst:
             -
                name: "default_name_61 (source firewall.address.name firewall.addrgrp.name)"
            dst_negate: "enable"
            dst6:
             -
                name: "default_name_64 (source firewall.address6.name firewall.addrgrp6.name)"
            end_port: "65"
            gateway: "enable"
            groups:
             -
                name: "default_name_68 (source user.group.name)"
            health_check: "<your_own_value> (source system.virtual-wan-link.health-check.name)"
            hold_down_time: "70"
            id:  "71"
            input_device:
             -
                name: "default_name_73 (source system.interface.name)"
            internet_service: "enable"
            internet_service_ctrl:
             -
                id:  "76"
            internet_service_ctrl_group:
             -
                name: "default_name_78 (source application.group.name)"
            internet_service_custom:
             -
                name: "default_name_80 (source firewall.internet-service-custom.name)"
            internet_service_custom_group:
             -
                name: "default_name_82 (source firewall.internet-service-custom-group.name)"
            internet_service_group:
             -
                name: "default_name_84 (source firewall.internet-service-group.name)"
            internet_service_id:
             -
                id:  "86 (source firewall.internet-service.id)"
            jitter_weight: "87"
            latency_weight: "88"
            link_cost_factor: "latency"
            link_cost_threshold: "90"
            member: "91"
            mode: "auto"
            name: "default_name_93"
            packet_loss_weight: "94"
            priority_members:
             -
                seq_num: "96 (source system.virtual-wan-link.members.seq-num)"
            protocol: "97"
            quality_link: "98"
            route_tag: "99"
            sla:
             -
                health_check: "<your_own_value> (source system.virtual-wan-link.health-check.name)"
                id:  "102"
            src:
             -
                name: "default_name_104 (source firewall.address.name firewall.addrgrp.name)"
            src_negate: "enable"
            src6:
             -
                name: "default_name_107 (source firewall.address6.name firewall.addrgrp6.name)"
            start_port: "108"
            status: "enable"
            tos: "<your_own_value>"
            tos_mask: "<your_own_value>"
            users:
             -
                name: "default_name_113 (source user.local.name)"
        status: "disable"
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


def filter_system_virtual_wan_link_data(json):
    option_list = ['fail_alert_interfaces', 'fail_detect', 'health_check',
                   'load_balance_mode', 'members', 'service',
                   'status']
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


def system_virtual_wan_link(data, fos):
    vdom = data['vdom']
    system_virtual_wan_link_data = data['system_virtual_wan_link']
    filtered_data = underscore_to_hyphen(filter_system_virtual_wan_link_data(system_virtual_wan_link_data))

    return fos.set('system',
                   'virtual-wan-link',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_virtual_wan_link']:
        resp = system_virtual_wan_link(data, fos)

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
        "system_virtual_wan_link": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "fail_alert_interfaces": {"required": False, "type": "list",
                                          "options": {
                                              "name": {"required": True, "type": "str"}
                                          }},
                "fail_detect": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "health_check": {"required": False, "type": "list",
                                 "options": {
                                     "addr_mode": {"required": False, "type": "str",
                                                   "choices": ["ipv4", "ipv6"]},
                                     "failtime": {"required": False, "type": "int"},
                                     "http_agent": {"required": False, "type": "str"},
                                     "http_get": {"required": False, "type": "str"},
                                     "http_match": {"required": False, "type": "str"},
                                     "interval": {"required": False, "type": "int"},
                                     "members": {"required": False, "type": "list",
                                                 "options": {
                                                     "seq_num": {"required": False, "type": "int"}
                                                 }},
                                     "name": {"required": True, "type": "str"},
                                     "packet_size": {"required": False, "type": "int"},
                                     "password": {"required": False, "type": "str", "no_log": True},
                                     "port": {"required": False, "type": "int"},
                                     "protocol": {"required": False, "type": "str",
                                                  "choices": ["ping", "tcp-echo", "udp-echo",
                                                              "http", "twamp", "ping6"]},
                                     "recoverytime": {"required": False, "type": "int"},
                                     "security_mode": {"required": False, "type": "str",
                                                       "choices": ["none", "authentication"]},
                                     "server": {"required": False, "type": "str"},
                                     "sla": {"required": False, "type": "list",
                                             "options": {
                                                 "id": {"required": True, "type": "int"},
                                                 "jitter_threshold": {"required": False, "type": "int"},
                                                 "latency_threshold": {"required": False, "type": "int"},
                                                 "link_cost_factor": {"required": False, "type": "str",
                                                                      "choices": ["latency", "jitter", "packet-loss"]},
                                                 "packetloss_threshold": {"required": False, "type": "int"}
                                             }},
                                     "threshold_alert_jitter": {"required": False, "type": "int"},
                                     "threshold_alert_latency": {"required": False, "type": "int"},
                                     "threshold_alert_packetloss": {"required": False, "type": "int"},
                                     "threshold_warning_jitter": {"required": False, "type": "int"},
                                     "threshold_warning_latency": {"required": False, "type": "int"},
                                     "threshold_warning_packetloss": {"required": False, "type": "int"},
                                     "update_cascade_interface": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                     "update_static_route": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]}
                                 }},
                "load_balance_mode": {"required": False, "type": "str",
                                      "choices": ["source-ip-based", "weight-based", "usage-based",
                                                  "source-dest-ip-based", "measured-volume-based"]},
                "members": {"required": False, "type": "list",
                            "options": {
                                "comment": {"required": False, "type": "str"},
                                "gateway": {"required": False, "type": "str"},
                                "gateway6": {"required": False, "type": "str"},
                                "ingress_spillover_threshold": {"required": False, "type": "int"},
                                "interface": {"required": False, "type": "str"},
                                "priority": {"required": False, "type": "int"},
                                "seq_num": {"required": False, "type": "int"},
                                "source": {"required": False, "type": "str"},
                                "source6": {"required": False, "type": "str"},
                                "spillover_threshold": {"required": False, "type": "int"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                                "volume_ratio": {"required": False, "type": "int"},
                                "weight": {"required": False, "type": "int"}
                            }},
                "service": {"required": False, "type": "list",
                            "options": {
                                "addr_mode": {"required": False, "type": "str",
                                              "choices": ["ipv4", "ipv6"]},
                                "bandwidth_weight": {"required": False, "type": "int"},
                                "default": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "dscp_forward": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                "dscp_forward_tag": {"required": False, "type": "str"},
                                "dscp_reverse": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                "dscp_reverse_tag": {"required": False, "type": "str"},
                                "dst": {"required": False, "type": "list",
                                        "options": {
                                            "name": {"required": True, "type": "str"}
                                        }},
                                "dst_negate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "dst6": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "end_port": {"required": False, "type": "int"},
                                "gateway": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "groups": {"required": False, "type": "list",
                                           "options": {
                                               "name": {"required": True, "type": "str"}
                                           }},
                                "health_check": {"required": False, "type": "str"},
                                "hold_down_time": {"required": False, "type": "int"},
                                "id": {"required": True, "type": "int"},
                                "input_device": {"required": False, "type": "list",
                                                 "options": {
                                                     "name": {"required": True, "type": "str"}
                                                 }},
                                "internet_service": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "internet_service_ctrl": {"required": False, "type": "list",
                                                          "options": {
                                                              "id": {"required": True, "type": "int"}
                                                          }},
                                "internet_service_ctrl_group": {"required": False, "type": "list",
                                                                "options": {
                                                                    "name": {"required": True, "type": "str"}
                                                                }},
                                "internet_service_custom": {"required": False, "type": "list",
                                                            "options": {
                                                                "name": {"required": True, "type": "str"}
                                                            }},
                                "internet_service_custom_group": {"required": False, "type": "list",
                                                                  "options": {
                                                                      "name": {"required": True, "type": "str"}
                                                                  }},
                                "internet_service_group": {"required": False, "type": "list",
                                                           "options": {
                                                               "name": {"required": True, "type": "str"}
                                                           }},
                                "internet_service_id": {"required": False, "type": "list",
                                                        "options": {
                                                            "id": {"required": True, "type": "int"}
                                                        }},
                                "jitter_weight": {"required": False, "type": "int"},
                                "latency_weight": {"required": False, "type": "int"},
                                "link_cost_factor": {"required": False, "type": "str",
                                                     "choices": ["latency", "jitter", "packet-loss",
                                                                 "inbandwidth", "outbandwidth", "bibandwidth",
                                                                 "custom-profile-1"]},
                                "link_cost_threshold": {"required": False, "type": "int"},
                                "member": {"required": False, "type": "int"},
                                "mode": {"required": False, "type": "str",
                                         "choices": ["auto", "manual", "priority",
                                                     "sla"]},
                                "name": {"required": False, "type": "str"},
                                "packet_loss_weight": {"required": False, "type": "int"},
                                "priority_members": {"required": False, "type": "list",
                                                     "options": {
                                                         "seq_num": {"required": False, "type": "int"}
                                                     }},
                                "protocol": {"required": False, "type": "int"},
                                "quality_link": {"required": False, "type": "int"},
                                "route_tag": {"required": False, "type": "int"},
                                "sla": {"required": False, "type": "list",
                                        "options": {
                                            "health_check": {"required": False, "type": "str"},
                                            "id": {"required": False, "type": "int"}
                                        }},
                                "src": {"required": False, "type": "list",
                                        "options": {
                                            "name": {"required": True, "type": "str"}
                                        }},
                                "src_negate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "src6": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "start_port": {"required": False, "type": "int"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                "tos": {"required": False, "type": "str"},
                                "tos_mask": {"required": False, "type": "str"},
                                "users": {"required": False, "type": "list",
                                          "options": {
                                              "name": {"required": True, "type": "str"}
                                          }}
                            }},
                "status": {"required": False, "type": "str",
                           "choices": ["disable", "enable"]}

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
