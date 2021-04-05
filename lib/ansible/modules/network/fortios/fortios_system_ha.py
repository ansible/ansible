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
module: fortios_system_ha
short_description: Configure HA in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS (FOS) device by allowing the
      user to set and modify system feature and ha category.
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
    system_ha:
        description:
            - Configure HA.
        default: null
        type: dict
        suboptions:
            arps:
                description:
                    - Number of gratuitous ARPs (1 - 60). Lower to reduce traffic. Higher to reduce failover time.
                type: int
            arps_interval:
                description:
                    - Time between gratuitous ARPs  (1 - 20 sec). Lower to reduce failover time. Higher to reduce traffic.
                type: int
            authentication:
                description:
                    - Enable/disable heartbeat message authentication.
                type: str
                choices:
                    - enable
                    - disable
            cpu_threshold:
                description:
                    - Dynamic weighted load balancing CPU usage weight and high and low thresholds.
                type: str
            encryption:
                description:
                    - Enable/disable heartbeat message encryption.
                type: str
                choices:
                    - enable
                    - disable
            ftp_proxy_threshold:
                description:
                    - Dynamic weighted load balancing weight and high and low number of FTP proxy sessions.
                type: str
            gratuitous_arps:
                description:
                    - Enable/disable gratuitous ARPs. Disable if link-failed-signal enabled.
                type: str
                choices:
                    - enable
                    - disable
            group_id:
                description:
                    - Cluster group ID  (0 - 255). Must be the same for all members.
                type: int
            group_name:
                description:
                    - Cluster group name. Must be the same for all members.
                type: str
            ha_direct:
                description:
                    - Enable/disable using ha-mgmt interface for syslog, SNMP, remote authentication (RADIUS), FortiAnalyzer, and FortiSandbox.
                type: str
                choices:
                    - enable
                    - disable
            ha_eth_type:
                description:
                    - HA heartbeat packet Ethertype (4-digit hex).
                type: str
            ha_mgmt_interfaces:
                description:
                    - Reserve interfaces to manage individual cluster units.
                type: list
                suboptions:
                    dst:
                        description:
                            - Default route destination for reserved HA management interface.
                        type: str
                    gateway:
                        description:
                            - Default route gateway for reserved HA management interface.
                        type: str
                    gateway6:
                        description:
                            - Default IPv6 gateway for reserved HA management interface.
                        type: str
                    id:
                        description:
                            - Table ID.
                        required: true
                        type: int
                    interface:
                        description:
                            - Interface to reserve for HA management. Source system.interface.name.
                        type: str
            ha_mgmt_status:
                description:
                    - Enable to reserve interfaces to manage individual cluster units.
                type: str
                choices:
                    - enable
                    - disable
            ha_uptime_diff_margin:
                description:
                    - Normally you would only reduce this value for failover testing.
                type: int
            hb_interval:
                description:
                    - Time between sending heartbeat packets (1 - 20 (100*ms)). Increase to reduce false positives.
                type: int
            hb_lost_threshold:
                description:
                    - Number of lost heartbeats to signal a failure (1 - 60). Increase to reduce false positives.
                type: int
            hbdev:
                description:
                    - Heartbeat interfaces. Must be the same for all members.
                type: str
            hc_eth_type:
                description:
                    - Transparent mode HA heartbeat packet Ethertype (4-digit hex).
                type: str
            hello_holddown:
                description:
                    - Time to wait before changing from hello to work state (5 - 300 sec).
                type: int
            http_proxy_threshold:
                description:
                    - Dynamic weighted load balancing weight and high and low number of HTTP proxy sessions.
                type: str
            imap_proxy_threshold:
                description:
                    - Dynamic weighted load balancing weight and high and low number of IMAP proxy sessions.
                type: str
            inter_cluster_session_sync:
                description:
                    - Enable/disable synchronization of sessions among HA clusters.
                type: str
                choices:
                    - enable
                    - disable
            key:
                description:
                    - key
                type: str
            l2ep_eth_type:
                description:
                    - Telnet session HA heartbeat packet Ethertype (4-digit hex).
                type: str
            link_failed_signal:
                description:
                    - Enable to shut down all interfaces for 1 sec after a failover. Use if gratuitous ARPs do not update network.
                type: str
                choices:
                    - enable
                    - disable
            load_balance_all:
                description:
                    - Enable to load balance TCP sessions. Disable to load balance proxy sessions only.
                type: str
                choices:
                    - enable
                    - disable
            memory_compatible_mode:
                description:
                    - Enable/disable memory compatible mode.
                type: str
                choices:
                    - enable
                    - disable
            memory_threshold:
                description:
                    - Dynamic weighted load balancing memory usage weight and high and low thresholds.
                type: str
            mode:
                description:
                    - HA mode. Must be the same for all members. FGSP requires standalone.
                type: str
                choices:
                    - standalone
                    - a-a
                    - a-p
            monitor:
                description:
                    - Interfaces to check for port monitoring (or link failure). Source system.interface.name.
                type: str
            multicast_ttl:
                description:
                    - HA multicast TTL on master (5 - 3600 sec).
                type: int
            nntp_proxy_threshold:
                description:
                    - Dynamic weighted load balancing weight and high and low number of NNTP proxy sessions.
                type: str
            override:
                description:
                    - Enable and increase the priority of the unit that should always be primary (master).
                type: str
                choices:
                    - enable
                    - disable
            override_wait_time:
                description:
                    - Delay negotiating if override is enabled (0 - 3600 sec). Reduces how often the cluster negotiates.
                type: int
            password:
                description:
                    - Cluster password. Must be the same for all members.
                type: str
            pingserver_failover_threshold:
                description:
                    - Remote IP monitoring failover threshold (0 - 50).
                type: int
            pingserver_flip_timeout:
                description:
                    - Time to wait in minutes before renegotiating after a remote IP monitoring failover.
                type: int
            pingserver_monitor_interface:
                description:
                    - Interfaces to check for remote IP monitoring. Source system.interface.name.
                type: str
            pingserver_slave_force_reset:
                description:
                    - Enable to force the cluster to negotiate after a remote IP monitoring failover.
                type: str
                choices:
                    - enable
                    - disable
            pop3_proxy_threshold:
                description:
                    - Dynamic weighted load balancing weight and high and low number of POP3 proxy sessions.
                type: str
            priority:
                description:
                    - Increase the priority to select the primary unit (0 - 255).
                type: int
            route_hold:
                description:
                    - Time to wait between routing table updates to the cluster (0 - 3600 sec).
                type: int
            route_ttl:
                description:
                    - TTL for primary unit routes (5 - 3600 sec). Increase to maintain active routes during failover.
                type: int
            route_wait:
                description:
                    - Time to wait before sending new routes to the cluster (0 - 3600 sec).
                type: int
            schedule:
                description:
                    - Type of A-A load balancing. Use none if you have external load balancers.
                type: str
                choices:
                    - none
                    - hub
                    - leastconnection
                    - round-robin
                    - weight-round-robin
                    - random
                    - ip
                    - ipport
            secondary_vcluster:
                description:
                    - Configure virtual cluster 2.
                type: dict
                suboptions:
                    monitor:
                        description:
                            - Interfaces to check for port monitoring (or link failure). Source system.interface.name.
                        type: str
                    override:
                        description:
                            - Enable and increase the priority of the unit that should always be primary (master).
                        type: str
                        choices:
                            - enable
                            - disable
                    override_wait_time:
                        description:
                            - Delay negotiating if override is enabled (0 - 3600 sec). Reduces how often the cluster negotiates.
                        type: int
                    pingserver_failover_threshold:
                        description:
                            - Remote IP monitoring failover threshold (0 - 50).
                        type: int
                    pingserver_monitor_interface:
                        description:
                            - Interfaces to check for remote IP monitoring. Source system.interface.name.
                        type: str
                    pingserver_slave_force_reset:
                        description:
                            - Enable to force the cluster to negotiate after a remote IP monitoring failover.
                        type: str
                        choices:
                            - enable
                            - disable
                    priority:
                        description:
                            - Increase the priority to select the primary unit (0 - 255).
                        type: int
                    vcluster_id:
                        description:
                            - Cluster ID.
                        type: int
                    vdom:
                        description:
                            - VDOMs in virtual cluster 2.
                        type: str
            session_pickup:
                description:
                    - Enable/disable session pickup. Enabling it can reduce session down time when fail over happens.
                type: str
                choices:
                    - enable
                    - disable
            session_pickup_connectionless:
                description:
                    - Enable/disable UDP and ICMP session sync for FGSP.
                type: str
                choices:
                    - enable
                    - disable
            session_pickup_delay:
                description:
                    - Enable to sync sessions longer than 30 sec. Only longer lived sessions need to be synced.
                type: str
                choices:
                    - enable
                    - disable
            session_pickup_expectation:
                description:
                    - Enable/disable session helper expectation session sync for FGSP.
                type: str
                choices:
                    - enable
                    - disable
            session_pickup_nat:
                description:
                    - Enable/disable NAT session sync for FGSP.
                type: str
                choices:
                    - enable
                    - disable
            session_sync_dev:
                description:
                    - Offload session sync to one or more interfaces to distribute traffic and prevent delays if needed. Source system.interface.name.
                type: str
            smtp_proxy_threshold:
                description:
                    - Dynamic weighted load balancing weight and high and low number of SMTP proxy sessions.
                type: str
            standalone_config_sync:
                description:
                    - Enable/disable FGSP configuration synchronization.
                type: str
                choices:
                    - enable
                    - disable
            standalone_mgmt_vdom:
                description:
                    - Enable/disable standalone management VDOM.
                type: str
                choices:
                    - enable
                    - disable
            sync_config:
                description:
                    - Enable/disable configuration synchronization.
                type: str
                choices:
                    - enable
                    - disable
            sync_packet_balance:
                description:
                    - Enable/disable HA packet distribution to multiple CPUs.
                type: str
                choices:
                    - enable
                    - disable
            unicast_hb:
                description:
                    - Enable/disable unicast heartbeat.
                type: str
                choices:
                    - enable
                    - disable
            unicast_hb_netmask:
                description:
                    - Unicast heartbeat netmask.
                type: str
            unicast_hb_peerip:
                description:
                    - Unicast heartbeat peer IP.
                type: str
            uninterruptible_upgrade:
                description:
                    - Enable to upgrade a cluster without blocking network traffic.
                type: str
                choices:
                    - enable
                    - disable
            vcluster_id:
                description:
                    - Cluster ID.
                type: int
            vcluster2:
                description:
                    - Enable/disable virtual cluster 2 for virtual clustering.
                type: str
                choices:
                    - enable
                    - disable
            vdom:
                description:
                    - VDOMs in virtual cluster 1.
                type: str
            weight:
                description:
                    - Weight-round-robin weight for each cluster unit. Syntax <priority> <weight>.
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
  - name: Configure HA.
    fortios_system_ha:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      https: "False"
      system_ha:
        arps: "3"
        arps_interval: "4"
        authentication: "enable"
        cpu_threshold: "<your_own_value>"
        encryption: "enable"
        ftp_proxy_threshold: "<your_own_value>"
        gratuitous_arps: "enable"
        group_id: "10"
        group_name: "<your_own_value>"
        ha_direct: "enable"
        ha_eth_type: "<your_own_value>"
        ha_mgmt_interfaces:
         -
            dst: "<your_own_value>"
            gateway: "<your_own_value>"
            gateway6: "<your_own_value>"
            id:  "18"
            interface: "<your_own_value> (source system.interface.name)"
        ha_mgmt_status: "enable"
        ha_uptime_diff_margin: "21"
        hb_interval: "22"
        hb_lost_threshold: "23"
        hbdev: "<your_own_value>"
        hc_eth_type: "<your_own_value>"
        hello_holddown: "26"
        http_proxy_threshold: "<your_own_value>"
        imap_proxy_threshold: "<your_own_value>"
        inter_cluster_session_sync: "enable"
        key: "<your_own_value>"
        l2ep_eth_type: "<your_own_value>"
        link_failed_signal: "enable"
        load_balance_all: "enable"
        memory_compatible_mode: "enable"
        memory_threshold: "<your_own_value>"
        mode: "standalone"
        monitor: "<your_own_value> (source system.interface.name)"
        multicast_ttl: "38"
        nntp_proxy_threshold: "<your_own_value>"
        override: "enable"
        override_wait_time: "41"
        password: "<your_own_value>"
        pingserver_failover_threshold: "43"
        pingserver_flip_timeout: "44"
        pingserver_monitor_interface: "<your_own_value> (source system.interface.name)"
        pingserver_slave_force_reset: "enable"
        pop3_proxy_threshold: "<your_own_value>"
        priority: "48"
        route_hold: "49"
        route_ttl: "50"
        route_wait: "51"
        schedule: "none"
        secondary_vcluster:
            monitor: "<your_own_value> (source system.interface.name)"
            override: "enable"
            override_wait_time: "56"
            pingserver_failover_threshold: "57"
            pingserver_monitor_interface: "<your_own_value> (source system.interface.name)"
            pingserver_slave_force_reset: "enable"
            priority: "60"
            vcluster_id: "61"
            vdom: "<your_own_value>"
        session_pickup: "enable"
        session_pickup_connectionless: "enable"
        session_pickup_delay: "enable"
        session_pickup_expectation: "enable"
        session_pickup_nat: "enable"
        session_sync_dev: "<your_own_value> (source system.interface.name)"
        smtp_proxy_threshold: "<your_own_value>"
        standalone_config_sync: "enable"
        standalone_mgmt_vdom: "enable"
        sync_config: "enable"
        sync_packet_balance: "enable"
        unicast_hb: "enable"
        unicast_hb_netmask: "<your_own_value>"
        unicast_hb_peerip: "<your_own_value>"
        uninterruptible_upgrade: "enable"
        vcluster_id: "78"
        vcluster2: "enable"
        vdom: "<your_own_value>"
        weight: "<your_own_value>"
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


def filter_system_ha_data(json):
    option_list = ['arps', 'arps_interval', 'authentication',
                   'cpu_threshold', 'encryption', 'ftp_proxy_threshold',
                   'gratuitous_arps', 'group_id', 'group_name',
                   'ha_direct', 'ha_eth_type', 'ha_mgmt_interfaces',
                   'ha_mgmt_status', 'ha_uptime_diff_margin', 'hb_interval',
                   'hb_lost_threshold', 'hbdev', 'hc_eth_type',
                   'hello_holddown', 'http_proxy_threshold', 'imap_proxy_threshold',
                   'inter_cluster_session_sync', 'key', 'l2ep_eth_type',
                   'link_failed_signal', 'load_balance_all', 'memory_compatible_mode',
                   'memory_threshold', 'mode', 'monitor',
                   'multicast_ttl', 'nntp_proxy_threshold', 'override',
                   'override_wait_time', 'password', 'pingserver_failover_threshold',
                   'pingserver_flip_timeout', 'pingserver_monitor_interface', 'pingserver_slave_force_reset',
                   'pop3_proxy_threshold', 'priority', 'route_hold',
                   'route_ttl', 'route_wait', 'schedule',
                   'secondary_vcluster', 'session_pickup', 'session_pickup_connectionless',
                   'session_pickup_delay', 'session_pickup_expectation', 'session_pickup_nat',
                   'session_sync_dev', 'smtp_proxy_threshold', 'standalone_config_sync',
                   'standalone_mgmt_vdom', 'sync_config', 'sync_packet_balance',
                   'unicast_hb', 'unicast_hb_netmask', 'unicast_hb_peerip',
                   'uninterruptible_upgrade', 'vcluster_id', 'vcluster2',
                   'vdom', 'weight']
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


def system_ha(data, fos):
    vdom = data['vdom']
    system_ha_data = data['system_ha']
    filtered_data = underscore_to_hyphen(filter_system_ha_data(system_ha_data))

    return fos.set('system',
                   'ha',
                   data=filtered_data,
                   vdom=vdom)


def is_successful_status(status):
    return status['status'] == "success" or \
        status['http_method'] == "DELETE" and status['http_status'] == 404


def fortios_system(data, fos):

    if data['system_ha']:
        resp = system_ha(data, fos)

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
        "system_ha": {
            "required": False, "type": "dict", "default": None,
            "options": {
                "arps": {"required": False, "type": "int"},
                "arps_interval": {"required": False, "type": "int"},
                "authentication": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "cpu_threshold": {"required": False, "type": "str"},
                "encryption": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "ftp_proxy_threshold": {"required": False, "type": "str"},
                "gratuitous_arps": {"required": False, "type": "str",
                                    "choices": ["enable", "disable"]},
                "group_id": {"required": False, "type": "int"},
                "group_name": {"required": False, "type": "str"},
                "ha_direct": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "ha_eth_type": {"required": False, "type": "str"},
                "ha_mgmt_interfaces": {"required": False, "type": "list",
                                       "options": {
                                           "dst": {"required": False, "type": "str"},
                                           "gateway": {"required": False, "type": "str"},
                                           "gateway6": {"required": False, "type": "str"},
                                           "id": {"required": True, "type": "int"},
                                           "interface": {"required": False, "type": "str"}
                                       }},
                "ha_mgmt_status": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "ha_uptime_diff_margin": {"required": False, "type": "int"},
                "hb_interval": {"required": False, "type": "int"},
                "hb_lost_threshold": {"required": False, "type": "int"},
                "hbdev": {"required": False, "type": "str"},
                "hc_eth_type": {"required": False, "type": "str"},
                "hello_holddown": {"required": False, "type": "int"},
                "http_proxy_threshold": {"required": False, "type": "str"},
                "imap_proxy_threshold": {"required": False, "type": "str"},
                "inter_cluster_session_sync": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "key": {"required": False, "type": "str"},
                "l2ep_eth_type": {"required": False, "type": "str"},
                "link_failed_signal": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "load_balance_all": {"required": False, "type": "str",
                                     "choices": ["enable", "disable"]},
                "memory_compatible_mode": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "memory_threshold": {"required": False, "type": "str"},
                "mode": {"required": False, "type": "str",
                         "choices": ["standalone", "a-a", "a-p"]},
                "monitor": {"required": False, "type": "str"},
                "multicast_ttl": {"required": False, "type": "int"},
                "nntp_proxy_threshold": {"required": False, "type": "str"},
                "override": {"required": False, "type": "str",
                             "choices": ["enable", "disable"]},
                "override_wait_time": {"required": False, "type": "int"},
                "password": {"required": False, "type": "str", "no_log": True},
                "pingserver_failover_threshold": {"required": False, "type": "int"},
                "pingserver_flip_timeout": {"required": False, "type": "int"},
                "pingserver_monitor_interface": {"required": False, "type": "str"},
                "pingserver_slave_force_reset": {"required": False, "type": "str",
                                                 "choices": ["enable", "disable"]},
                "pop3_proxy_threshold": {"required": False, "type": "str"},
                "priority": {"required": False, "type": "int"},
                "route_hold": {"required": False, "type": "int"},
                "route_ttl": {"required": False, "type": "int"},
                "route_wait": {"required": False, "type": "int"},
                "schedule": {"required": False, "type": "str",
                             "choices": ["none", "hub", "leastconnection",
                                         "round-robin", "weight-round-robin", "random",
                                         "ip", "ipport"]},
                "secondary_vcluster": {"required": False, "type": "dict",
                                       "options": {
                                           "monitor": {"required": False, "type": "str"},
                                           "override": {"required": False, "type": "str",
                                                        "choices": ["enable", "disable"]},
                                           "override_wait_time": {"required": False, "type": "int"},
                                           "pingserver_failover_threshold": {"required": False, "type": "int"},
                                           "pingserver_monitor_interface": {"required": False, "type": "str"},
                                           "pingserver_slave_force_reset": {"required": False, "type": "str",
                                                                            "choices": ["enable", "disable"]},
                                           "priority": {"required": False, "type": "int"},
                                           "vcluster_id": {"required": False, "type": "int"},
                                           "vdom": {"required": False, "type": "str"}
                                       }},
                "session_pickup": {"required": False, "type": "str",
                                   "choices": ["enable", "disable"]},
                "session_pickup_connectionless": {"required": False, "type": "str",
                                                  "choices": ["enable", "disable"]},
                "session_pickup_delay": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "session_pickup_expectation": {"required": False, "type": "str",
                                               "choices": ["enable", "disable"]},
                "session_pickup_nat": {"required": False, "type": "str",
                                       "choices": ["enable", "disable"]},
                "session_sync_dev": {"required": False, "type": "str"},
                "smtp_proxy_threshold": {"required": False, "type": "str"},
                "standalone_config_sync": {"required": False, "type": "str",
                                           "choices": ["enable", "disable"]},
                "standalone_mgmt_vdom": {"required": False, "type": "str",
                                         "choices": ["enable", "disable"]},
                "sync_config": {"required": False, "type": "str",
                                "choices": ["enable", "disable"]},
                "sync_packet_balance": {"required": False, "type": "str",
                                        "choices": ["enable", "disable"]},
                "unicast_hb": {"required": False, "type": "str",
                               "choices": ["enable", "disable"]},
                "unicast_hb_netmask": {"required": False, "type": "str"},
                "unicast_hb_peerip": {"required": False, "type": "str"},
                "uninterruptible_upgrade": {"required": False, "type": "str",
                                            "choices": ["enable", "disable"]},
                "vcluster_id": {"required": False, "type": "int"},
                "vcluster2": {"required": False, "type": "str",
                              "choices": ["enable", "disable"]},
                "vdom": {"required": False, "type": "str"},
                "weight": {"required": False, "type": "str"}

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
