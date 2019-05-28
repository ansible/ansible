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
    - This module is able to configure a FortiGate or FortiOS by allowing the
      user to set and modify system feature and virtual_wan_link category.
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
    system_virtual_wan_link:
        description:
            - Configure redundant internet connections using SD-WAN (formerly virtual WAN link).
        default: null
        suboptions:
            fail-alert-interfaces:
                description:
                    - Physical interfaces that will be alerted.
                suboptions:
                    name:
                        description:
                            - Physical interface name. Source system.interface.name.
                        required: true
            fail-detect:
                description:
                    - Enable/disable SD-WAN Internet connection status checking (failure detection).
                choices:
                    - enable
                    - disable
            health-check:
                description:
                    - SD-WAN status checking or health checking. Identify a server on the Internet and determine how SD-WAN verifies that the FortiGate can
                       communicate with it.
                suboptions:
                    addr-mode:
                        description:
                            - Address mode (IPv4 or IPv6).
                        choices:
                            - ipv4
                            - ipv6
                    failtime:
                        description:
                            - Number of failures before server is considered lost (1 - 10, default = 5).
                    http-get:
                        description:
                            - URL used to communicate with the server if the protocol if the protocol is HTTP.
                    http-match:
                        description:
                            - Response string expected from the server if the protocol is HTTP.
                    interval:
                        description:
                            - Status check interval, or the time between attempting to connect to the server (1 - 3600 sec, default = 5).
                    members:
                        description:
                            - Member sequence number list.
                        suboptions:
                            seq-num:
                                description:
                                    - Member sequence number. Source system.virtual-wan-link.members.seq-num.
                                required: true
                    name:
                        description:
                            - Status check or health check name.
                        required: true
                    packet-size:
                        description:
                            - Packet size of a twamp test session,
                    password:
                        description:
                            - Twamp controller password in authentication mode
                    port:
                        description:
                            - Port number used to communicate with the server over the selected protocol.
                    protocol:
                        description:
                            - Protocol used to determine if the FortiGate can communicate with the server.
                        choices:
                            - ping
                            - tcp-echo
                            - udp-echo
                            - http
                            - twamp
                            - ping6
                    recoverytime:
                        description:
                            - Number of successful responses received before server is considered recovered (1 - 10, default = 5).
                    security-mode:
                        description:
                            - Twamp controller security mode.
                        choices:
                            - none
                            - authentication
                    server:
                        description:
                            - IP address or FQDN name of the server.
                    sla:
                        description:
                            - Service level agreement (SLA).
                        suboptions:
                            id:
                                description:
                                    - SLA ID.
                                required: true
                            jitter-threshold:
                                description:
                                    - Jitter for SLA to make decision in milliseconds. (0 - 10000000, default = 5).
                            latency-threshold:
                                description:
                                    - Latency for SLA to make decision in milliseconds. (0 - 10000000, default = 5).
                            link-cost-factor:
                                description:
                                    - Criteria on which to base link selection.
                                choices:
                                    - latency
                                    - jitter
                                    - packet-loss
                            packetloss-threshold:
                                description:
                                    - Packet loss for SLA to make decision in percentage. (0 - 100, default = 0).
                    threshold-alert-jitter:
                        description:
                            - Alert threshold for jitter (ms, default = 0).
                    threshold-alert-latency:
                        description:
                            - Alert threshold for latency (ms, default = 0).
                    threshold-alert-packetloss:
                        description:
                            - Alert threshold for packet loss (percentage, default = 0).
                    threshold-warning-jitter:
                        description:
                            - Warning threshold for jitter (ms, default = 0).
                    threshold-warning-latency:
                        description:
                            - Warning threshold for latency (ms, default = 0).
                    threshold-warning-packetloss:
                        description:
                            - Warning threshold for packet loss (percentage, default = 0).
                    update-cascade-interface:
                        description:
                            - Enable/disable update cascade interface.
                        choices:
                            - enable
                            - disable
                    update-static-route:
                        description:
                            - Enable/disable updating the static route.
                        choices:
                            - enable
                            - disable
            load-balance-mode:
                description:
                    - Algorithm or mode to use for load balancing Internet traffic to SD-WAN members.
                choices:
                    - source-ip-based
                    - weight-based
                    - usage-based
                    - source-dest-ip-based
                    - measured-volume-based
            members:
                description:
                    - Physical FortiGate interfaces added to the virtual-wan-link.
                suboptions:
                    comment:
                        description:
                            - Comments.
                    gateway:
                        description:
                            - The default gateway for this interface. Usually the default gateway of the Internet service provider that this interface is
                               connected to.
                    gateway6:
                        description:
                            - IPv6 gateway.
                    ingress-spillover-threshold:
                        description:
                            - Ingress spillover threshold for this interface (0 - 16776000 kbit/s). When this traffic volume threshold is reached, new
                               sessions spill over to other interfaces in the SD-WAN.
                    interface:
                        description:
                            - Interface name. Source system.interface.name.
                    priority:
                        description:
                            - Priority of the interface (0 - 4294967295). Used for SD-WAN rules or priority rules.
                    seq-num:
                        description:
                            - Sequence number(1-255).
                        required: true
                    source:
                        description:
                            - Source IP address used in the health-check packet to the server.
                    source6:
                        description:
                            - Source IPv6 address used in the health-check packet to the server.
                    spillover-threshold:
                        description:
                            - Egress spillover threshold for this interface (0 - 16776000 kbit/s). When this traffic volume threshold is reached, new sessions
                               spill over to other interfaces in the SD-WAN.
                    status:
                        description:
                            - Enable/disable this interface in the SD-WAN.
                        choices:
                            - disable
                            - enable
                    volume-ratio:
                        description:
                            - Measured volume ratio (this value / sum of all values = percentage of link volume, 0 - 255).
                    weight:
                        description:
                            - Weight of this interface for weighted load balancing. (0 - 255) More traffic is directed to interfaces with higher weights.
            service:
                description:
                    - Create SD-WAN rules or priority rules (also called services) to control how sessions are distributed to physical interfaces in the
                       SD-WAN.
                suboptions:
                    addr-mode:
                        description:
                            - Address mode (IPv4 or IPv6).
                        choices:
                            - ipv4
                            - ipv6
                    bandwidth-weight:
                        description:
                            - Coefficient of reciprocal of available bidirectional bandwidth in the formula of custom-profile-1.
                    dscp-forward:
                        description:
                            - Enable/disable forward traffic DSCP tag.
                        choices:
                            - enable
                            - disable
                    dscp-forward-tag:
                        description:
                            - Forward traffic DSCP tag.
                    dscp-reverse:
                        description:
                            - Enable/disable reverse traffic DSCP tag.
                        choices:
                            - enable
                            - disable
                    dscp-reverse-tag:
                        description:
                            - Reverse traffic DSCP tag.
                    dst:
                        description:
                            - Destination address name.
                        suboptions:
                            name:
                                description:
                                    - Address or address group name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                    dst-negate:
                        description:
                            - Enable/disable negation of destination address match.
                        choices:
                            - enable
                            - disable
                    dst6:
                        description:
                            - Destination address6 name.
                        suboptions:
                            name:
                                description:
                                    - Address6 or address6 group name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                    end-port:
                        description:
                            - End destination port number.
                    gateway:
                        description:
                            - Enable/disable SD-WAN service gateway.
                        choices:
                            - enable
                            - disable
                    groups:
                        description:
                            - User groups.
                        suboptions:
                            name:
                                description:
                                    - Group name. Source user.group.name.
                                required: true
                    health-check:
                        description:
                            - Health check. Source system.virtual-wan-link.health-check.name.
                    hold-down-time:
                        description:
                            - Waiting period in seconds when switching from the back-up member to the primary member (0 - 10000000, default = 0).
                    id:
                        description:
                            - Priority rule ID (1 - 4000).
                        required: true
                    input-device:
                        description:
                            - Source interface name.
                        suboptions:
                            name:
                                description:
                                    - Interface name. Source system.interface.name.
                                required: true
                    internet-service:
                        description:
                            - Enable/disable use of Internet service for application-based load balancing.
                        choices:
                            - enable
                            - disable
                    internet-service-ctrl:
                        description:
                            - Control-based Internet Service ID list.
                        suboptions:
                            id:
                                description:
                                    - Control-based Internet Service ID.
                                required: true
                    internet-service-ctrl-group:
                        description:
                            - Control-based Internet Service group list.
                        suboptions:
                            name:
                                description:
                                    - Control-based Internet Service group name. Source application.group.name.
                                required: true
                    internet-service-custom:
                        description:
                            - Custom Internet service name list.
                        suboptions:
                            name:
                                description:
                                    - Custom Internet service name. Source firewall.internet-service-custom.name.
                                required: true
                    internet-service-custom-group:
                        description:
                            - Custom Internet Service group list.
                        suboptions:
                            name:
                                description:
                                    - Custom Internet Service group name. Source firewall.internet-service-custom-group.name.
                                required: true
                    internet-service-group:
                        description:
                            - Internet Service group list.
                        suboptions:
                            name:
                                description:
                                    - Internet Service group name. Source firewall.internet-service-group.name.
                                required: true
                    internet-service-id:
                        description:
                            - Internet service ID list.
                        suboptions:
                            id:
                                description:
                                    - Internet service ID. Source firewall.internet-service.id.
                                required: true
                    jitter-weight:
                        description:
                            - Coefficient of jitter in the formula of custom-profile-1.
                    latency-weight:
                        description:
                            - Coefficient of latency in the formula of custom-profile-1.
                    link-cost-factor:
                        description:
                            - Link cost factor.
                        choices:
                            - latency
                            - jitter
                            - packet-loss
                            - inbandwidth
                            - outbandwidth
                            - bibandwidth
                            - custom-profile-1
                    link-cost-threshold:
                        description:
                            - Percentage threshold change of link cost values that will result in policy route regeneration (0 - 10000000, default = 10).
                    member:
                        description:
                            - Member sequence number.
                    mode:
                        description:
                            - Control how the priority rule sets the priority of interfaces in the SD-WAN.
                        choices:
                            - auto
                            - manual
                            - priority
                            - sla
                    name:
                        description:
                            - Priority rule name.
                    packet-loss-weight:
                        description:
                            - Coefficient of packet-loss in the formula of custom-profile-1.
                    priority-members:
                        description:
                            - Member sequence number list.
                        suboptions:
                            seq-num:
                                description:
                                    - Member sequence number. Source system.virtual-wan-link.members.seq-num.
                                required: true
                    protocol:
                        description:
                            - Protocol number.
                    quality-link:
                        description:
                            - Quality grade.
                    route-tag:
                        description:
                            - IPv4 route map route-tag.
                    sla:
                        description:
                            - Service level agreement (SLA).
                        suboptions:
                            health-check:
                                description:
                                    - Virtual WAN Link health-check. Source system.virtual-wan-link.health-check.name.
                                required: true
                            id:
                                description:
                                    - SLA ID.
                    src:
                        description:
                            - Source address name.
                        suboptions:
                            name:
                                description:
                                    - Address or address group name. Source firewall.address.name firewall.addrgrp.name.
                                required: true
                    src-negate:
                        description:
                            - Enable/disable negation of source address match.
                        choices:
                            - enable
                            - disable
                    src6:
                        description:
                            - Source address6 name.
                        suboptions:
                            name:
                                description:
                                    - Address6 or address6 group name. Source firewall.address6.name firewall.addrgrp6.name.
                                required: true
                    start-port:
                        description:
                            - Start destination port number.
                    status:
                        description:
                            - Enable/disable SD-WAN service.
                        choices:
                            - enable
                            - disable
                    tos:
                        description:
                            - Type of service bit pattern.
                    tos-mask:
                        description:
                            - Type of service evaluated bits.
                    users:
                        description:
                            - User name.
                        suboptions:
                            name:
                                description:
                                    - User name. Source user.local.name.
                                required: true
            status:
                description:
                    - Enable/disable SD-WAN.
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
  tasks:
  - name: Configure redundant internet connections using SD-WAN (formerly virtual WAN link).
    fortios_system_virtual_wan_link:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_virtual_wan_link:
        fail-alert-interfaces:
         -
            name: "default_name_4 (source system.interface.name)"
        fail-detect: "enable"
        health-check:
         -
            addr-mode: "ipv4"
            failtime: "8"
            http-get: "<your_own_value>"
            http-match: "<your_own_value>"
            interval: "11"
            members:
             -
                seq-num: "13 (source system.virtual-wan-link.members.seq-num)"
            name: "default_name_14"
            packet-size: "15"
            password: "<your_own_value>"
            port: "17"
            protocol: "ping"
            recoverytime: "19"
            security-mode: "none"
            server: "192.168.100.40"
            sla:
             -
                id:  "23"
                jitter-threshold: "24"
                latency-threshold: "25"
                link-cost-factor: "latency"
                packetloss-threshold: "27"
            threshold-alert-jitter: "28"
            threshold-alert-latency: "29"
            threshold-alert-packetloss: "30"
            threshold-warning-jitter: "31"
            threshold-warning-latency: "32"
            threshold-warning-packetloss: "33"
            update-cascade-interface: "enable"
            update-static-route: "enable"
        load-balance-mode: "source-ip-based"
        members:
         -
            comment: "Comments."
            gateway: "<your_own_value>"
            gateway6: "<your_own_value>"
            ingress-spillover-threshold: "41"
            interface: "<your_own_value> (source system.interface.name)"
            priority: "43"
            seq-num: "44"
            source: "<your_own_value>"
            source6: "<your_own_value>"
            spillover-threshold: "47"
            status: "disable"
            volume-ratio: "49"
            weight: "50"
        service:
         -
            addr-mode: "ipv4"
            bandwidth-weight: "53"
            dscp-forward: "enable"
            dscp-forward-tag: "<your_own_value>"
            dscp-reverse: "enable"
            dscp-reverse-tag: "<your_own_value>"
            dst:
             -
                name: "default_name_59 (source firewall.address.name firewall.addrgrp.name)"
            dst-negate: "enable"
            dst6:
             -
                name: "default_name_62 (source firewall.address6.name firewall.addrgrp6.name)"
            end-port: "63"
            gateway: "enable"
            groups:
             -
                name: "default_name_66 (source user.group.name)"
            health-check: "<your_own_value> (source system.virtual-wan-link.health-check.name)"
            hold-down-time: "68"
            id:  "69"
            input-device:
             -
                name: "default_name_71 (source system.interface.name)"
            internet-service: "enable"
            internet-service-ctrl:
             -
                id:  "74"
            internet-service-ctrl-group:
             -
                name: "default_name_76 (source application.group.name)"
            internet-service-custom:
             -
                name: "default_name_78 (source firewall.internet-service-custom.name)"
            internet-service-custom-group:
             -
                name: "default_name_80 (source firewall.internet-service-custom-group.name)"
            internet-service-group:
             -
                name: "default_name_82 (source firewall.internet-service-group.name)"
            internet-service-id:
             -
                id:  "84 (source firewall.internet-service.id)"
            jitter-weight: "85"
            latency-weight: "86"
            link-cost-factor: "latency"
            link-cost-threshold: "88"
            member: "89"
            mode: "auto"
            name: "default_name_91"
            packet-loss-weight: "92"
            priority-members:
             -
                seq-num: "94 (source system.virtual-wan-link.members.seq-num)"
            protocol: "95"
            quality-link: "96"
            route-tag: "97"
            sla:
             -
                health-check: "<your_own_value> (source system.virtual-wan-link.health-check.name)"
                id:  "100"
            src:
             -
                name: "default_name_102 (source firewall.address.name firewall.addrgrp.name)"
            src-negate: "enable"
            src6:
             -
                name: "default_name_105 (source firewall.address6.name firewall.addrgrp6.name)"
            start-port: "106"
            status: "enable"
            tos: "<your_own_value>"
            tos-mask: "<your_own_value>"
            users:
             -
                name: "default_name_111 (source user.local.name)"
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


def filter_system_virtual_wan_link_data(json):
    option_list = ['fail-alert-interfaces', 'fail-detect', 'health-check',
                   'load-balance-mode', 'members', 'service',
                   'status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def system_virtual_wan_link(data, fos):
    vdom = data['vdom']
    system_virtual_wan_link_data = data['system_virtual_wan_link']
    filtered_data = filter_system_virtual_wan_link_data(system_virtual_wan_link_data)

    return fos.set('system',
                   'virtual-wan-link',
                   data=filtered_data,
                   vdom=vdom)


def fortios_system(data, fos):
    login(data, fos)

    if data['system_virtual_wan_link']:
        resp = system_virtual_wan_link(data, fos)

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": True},
        "system_virtual_wan_link": {
            "required": False, "type": "dict",
            "options": {
                "fail-alert-interfaces": {"required": False, "type": "list",
                                          "options": {
                                              "name": {"required": True, "type": "str"}
                                          }},
                "fail-detect": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "health-check": {"required": False, "type": "list",
                                 "options": {
                                     "addr-mode": {"required": False, "type": "str",
                                                   "choices": ["ipv4", "ipv6"]},
                                     "failtime": {"required": False, "type": "int"},
                                     "http-get": {"required": False, "type": "str"},
                                     "http-match": {"required": False, "type": "str"},
                                     "interval": {"required": False, "type": "int"},
                                     "members": {"required": False, "type": "list",
                                                 "options": {
                                                     "seq-num": {"required": True, "type": "int"}
                                                 }},
                                     "name": {"required": True, "type": "str"},
                                     "packet-size": {"required": False, "type": "int"},
                                     "password": {"required": False, "type": "str"},
                                     "port": {"required": False, "type": "int"},
                                     "protocol": {"required": False, "type": "str",
                                                  "choices": ["ping", "tcp-echo", "udp-echo",
                                                              "http", "twamp", "ping6"]},
                                     "recoverytime": {"required": False, "type": "int"},
                                     "security-mode": {"required": False, "type": "str",
                                                       "choices": ["none", "authentication"]},
                                     "server": {"required": False, "type": "str"},
                                     "sla": {"required": False, "type": "list",
                                             "options": {
                                                 "id": {"required": True, "type": "int"},
                                                 "jitter-threshold": {"required": False, "type": "int"},
                                                 "latency-threshold": {"required": False, "type": "int"},
                                                 "link-cost-factor": {"required": False, "type": "str",
                                                                      "choices": ["latency", "jitter", "packet-loss"]},
                                                 "packetloss-threshold": {"required": False, "type": "int"}
                                             }},
                                     "threshold-alert-jitter": {"required": False, "type": "int"},
                                     "threshold-alert-latency": {"required": False, "type": "int"},
                                     "threshold-alert-packetloss": {"required": False, "type": "int"},
                                     "threshold-warning-jitter": {"required": False, "type": "int"},
                                     "threshold-warning-latency": {"required": False, "type": "int"},
                                     "threshold-warning-packetloss": {"required": False, "type": "int"},
                                     "update-cascade-interface": {"required": False, "type": "str",
                                                                  "choices": ["enable", "disable"]},
                                     "update-static-route": {"required": False, "type": "str",
                                                             "choices": ["enable", "disable"]}
                                 }},
                "load-balance-mode": {"required": False, "type": "str",
                                      "choices": ["source-ip-based", "weight-based", "usage-based",
                                                  "source-dest-ip-based", "measured-volume-based"]},
                "members": {"required": False, "type": "list",
                            "options": {
                                "comment": {"required": False, "type": "str"},
                                "gateway": {"required": False, "type": "str"},
                                "gateway6": {"required": False, "type": "str"},
                                "ingress-spillover-threshold": {"required": False, "type": "int"},
                                "interface": {"required": False, "type": "str"},
                                "priority": {"required": False, "type": "int"},
                                "seq-num": {"required": True, "type": "int"},
                                "source": {"required": False, "type": "str"},
                                "source6": {"required": False, "type": "str"},
                                "spillover-threshold": {"required": False, "type": "int"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["disable", "enable"]},
                                "volume-ratio": {"required": False, "type": "int"},
                                "weight": {"required": False, "type": "int"}
                            }},
                "service": {"required": False, "type": "list",
                            "options": {
                                "addr-mode": {"required": False, "type": "str",
                                              "choices": ["ipv4", "ipv6"]},
                                "bandwidth-weight": {"required": False, "type": "int"},
                                "dscp-forward": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                "dscp-forward-tag": {"required": False, "type": "str"},
                                "dscp-reverse": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                                "dscp-reverse-tag": {"required": False, "type": "str"},
                                "dst": {"required": False, "type": "list",
                                        "options": {
                                            "name": {"required": True, "type": "str"}
                                        }},
                                "dst-negate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "dst6": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "end-port": {"required": False, "type": "int"},
                                "gateway": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                                "groups": {"required": False, "type": "list",
                                           "options": {
                                               "name": {"required": True, "type": "str"}
                                           }},
                                "health-check": {"required": False, "type": "str"},
                                "hold-down-time": {"required": False, "type": "int"},
                                "id": {"required": True, "type": "int"},
                                "input-device": {"required": False, "type": "list",
                                                 "options": {
                                                     "name": {"required": True, "type": "str"}
                                                 }},
                                "internet-service": {"required": False, "type": "str",
                                                     "choices": ["enable", "disable"]},
                                "internet-service-ctrl": {"required": False, "type": "list",
                                                          "options": {
                                                              "id": {"required": True, "type": "int"}
                                                          }},
                                "internet-service-ctrl-group": {"required": False, "type": "list",
                                                                "options": {
                                                                    "name": {"required": True, "type": "str"}
                                                                }},
                                "internet-service-custom": {"required": False, "type": "list",
                                                            "options": {
                                                                "name": {"required": True, "type": "str"}
                                                            }},
                                "internet-service-custom-group": {"required": False, "type": "list",
                                                                  "options": {
                                                                      "name": {"required": True, "type": "str"}
                                                                  }},
                                "internet-service-group": {"required": False, "type": "list",
                                                           "options": {
                                                               "name": {"required": True, "type": "str"}
                                                           }},
                                "internet-service-id": {"required": False, "type": "list",
                                                        "options": {
                                                            "id": {"required": True, "type": "int"}
                                                        }},
                                "jitter-weight": {"required": False, "type": "int"},
                                "latency-weight": {"required": False, "type": "int"},
                                "link-cost-factor": {"required": False, "type": "str",
                                                     "choices": ["latency", "jitter", "packet-loss",
                                                                 "inbandwidth", "outbandwidth", "bibandwidth",
                                                                 "custom-profile-1"]},
                                "link-cost-threshold": {"required": False, "type": "int"},
                                "member": {"required": False, "type": "int"},
                                "mode": {"required": False, "type": "str",
                                         "choices": ["auto", "manual", "priority",
                                                     "sla"]},
                                "name": {"required": False, "type": "str"},
                                "packet-loss-weight": {"required": False, "type": "int"},
                                "priority-members": {"required": False, "type": "list",
                                                     "options": {
                                                         "seq-num": {"required": True, "type": "int"}
                                                     }},
                                "protocol": {"required": False, "type": "int"},
                                "quality-link": {"required": False, "type": "int"},
                                "route-tag": {"required": False, "type": "int"},
                                "sla": {"required": False, "type": "list",
                                        "options": {
                                            "health-check": {"required": True, "type": "str"},
                                            "id": {"required": False, "type": "int"}
                                        }},
                                "src": {"required": False, "type": "list",
                                        "options": {
                                            "name": {"required": True, "type": "str"}
                                        }},
                                "src-negate": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                                "src6": {"required": False, "type": "list",
                                         "options": {
                                             "name": {"required": True, "type": "str"}
                                         }},
                                "start-port": {"required": False, "type": "int"},
                                "status": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                                "tos": {"required": False, "type": "str"},
                                "tos-mask": {"required": False, "type": "str"},
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
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_system(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
