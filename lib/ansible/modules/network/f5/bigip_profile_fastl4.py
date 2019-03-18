#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_profile_fastl4
short_description: Manages Fast L4 profiles
description:
  - Manages Fast L4 profiles.
version_added: 2.8
options:
  name:
    description:
      - Specifies the name of the profile.
    type: str
    required: True
  parent:
    description:
      - Specifies the profile from which this profile inherits settings.
      - When creating a new profile, if this parameter is not specified, the default
        is the system-supplied C(fastL4) profile.
    type: str
  idle_timeout:
    description:
      - Specifies the length of time that a connection is idle (has no traffic) before
        the connection is eligible for deletion.
      - When creating a new profile, if this parameter is not specified, the remote
        device will choose a default value appropriate for the profile, based on its
        C(parent) profile.
      - When a number is specified, indicates the number of seconds that the TCP
        connection can remain idle before the system deletes it.
      - When C(indefinite), specifies that the system does not delete TCP connections
        regardless of how long they remain idle.
      - When C(0), or C(immediate), specifies that the system deletes connections
        immediately when they become idle.
    type: str
  client_timeout:
    description:
      - Specifies a timeout for Late Binding.
      - This is the time limit for the client to provide the application data required to
        select a back-end server. That is, this is the maximum time that the BIG-IP system
        waits for information about the sender and the target.
      - This information typically arrives at the beginning of the FIX logon packet.
      - When C(0), or C(immediate), allows for no time beyond the moment of the first packet
        transmission.
      - When C(indefinite), disables the limit. This allows the client unlimited time
        to send the sender and target information.
    type: str
  description:
    description:
      - Description of the profile.
    type: str
  explicit_flow_migration:
    description:
      - Specifies whether a qualified late-binding connection requires an explicit iRule
        command to migrate down to ePVA hardware.
      - When C(no), a late-binding connection migrates down to ePVA immediately after
        establishing the server-side connection.
      - When C(yes), this parameter stops automatic migration to ePVA, and requires that
        the iRule explicitly trigger ePVA processing by invoking the C(release_flow)
        iRule command. This allows an iRule author to control when the connection uses the
        ePVA hardware.
    type: bool
  ip_df_mode:
    description:
      - Specifies the Don't Fragment (DF) bit setting in the IP Header of the outgoing TCP packet.
      - When C(pmtu), sets the outgoing IP Header DF bit based on IP pmtu setting.
      - When C(preserve), sets the outgoing Packet's IP Header DF bit to be same as incoming IP
        Header DF bit.
      - When C(set), sets the outgoing packet's IP Header DF bit.
      - When C(clear), clears the outgoing packet's IP Header DF bit.
    type: str
    choices:
      - pmtu
      - preserve
      - set
      - clear
  ip_tos_to_client:
    description:
      - Specifies, for IP traffic passing through the system to clients, whether the system
        modifies the IP type-of-service (ToS) setting in an IP packet header.
      - May be a number between 0 and 255 (inclusive). When a number, specifies the IP ToS
        setting that the system inserts in the IP packet header.
      - When C(pass-through), specifies that the IP ToS setting remains unchanged.
      - When C(mimic), specifies that the system sets the ToS level of outgoing packets to
        the same ToS level of the most-recently received incoming packet.
    type: str
  ip_tos_to_server:
    description:
      - Specifies, for IP traffic passing through the system to back-end servers, whether
        the system modifies the IP type-of-service (ToS) setting in an IP packet header.
      - May be a number between 0 and 255 (inclusive). When a number, specifies the IP ToS
        setting that the system inserts in the IP packet header.
      - When C(pass-through), specifies that the IP ToS setting remains unchanged.
      - When C(mimic), specifies that the system sets the ToS level of outgoing packets to
        the same ToS level of the most-recently received incoming packet.
    type: str
  ip_ttl_mode:
    description:
      - Specifies the outgoing TCP packet's IP Header TTL mode.
      - When C(proxy), sets the outgoing IP Header TTL value to 255/64 for IPv4/IPv6 respectively.
      - When C(preserve), sets the outgoing IP Header TTL value to be same as the incoming
        IP Header TTL value.
      - When C(decrement), sets the outgoing IP Header TTL value to be one less than the
        incoming TTL value.
      - When C(set), sets the outgoing IP Header TTL value to a specific value(as specified
        by C(ip_ttl_v4) or C(ip_ttl_v6).
    type: str
    choices:
      - proxy
      - preserve
      - decrement
      - set
  ip_ttl_v4:
    description:
      - Specifies the outgoing packet's IP Header TTL value for IPv4 traffic.
      - Maximum TTL value that can be specified is 255.
    type: int
  ip_ttl_v6:
    description:
      - Specifies the outgoing packet's IP Header TTL value for IPv6 traffic.
      - Maximum TTL value that can be specified is 255.
    type: int
  keep_alive_interval:
    description:
      - Specifies the keep-alive probe interval, in seconds.
    type: int
  late_binding:
    description:
      - Enables intelligent selection of a back-end server or pool, using an
        iRule to make the selection.
    type: bool
  link_qos_to_client:
    description:
      - Specifies, for IP traffic passing through the system to clients,
        whether the system modifies the link quality-of-service (QoS) setting
        in an IP packet header.
      - The link QoS value prioritizes the IP packet relative to other Layer
        2 traffic.
      - You can specify a number between 0 (lowest priority) and 7 (highest priority).
      - When a number, specifies the link QoS setting that the system inserts
        in the IP packet header.
      - When C(pass-through), specifies that the link QoS setting remains unchanged.
    type: str
  link_qos_to_server:
    description:
      - Specifies, for IP traffic passing through the system to back-end servers,
        whether the system modifies the link quality-of-service (QoS) setting
        in an IP packet header.
      - The link QoS value prioritizes the IP packet relative to other Layer
        2 traffic.
      - You can specify a number between 0 (lowest priority) and 7 (highest priority).
      - When a number, specifies the link QoS setting that the system inserts
        in the IP packet header.
      - When C(pass-through), specifies that the link QoS setting remains unchanged.
    type: str
  loose_close:
    description:
      - When C(yes), specifies, that the system closes a loosely-initiated connection
        when the system receives the first FIN packet from either the client or the server.
    type: bool
  loose_initialization:
    description:
      - When C(yes), specifies that the system initializes a connection when it
        receives any TCP packet, rather that requiring a SYN packet for connection
        initiation.
    type: bool
  mss_override:
    description:
      - Specifies a maximum segment size (MSS) override for server-side connections.
      - Valid range is 256 to 9162 or 0 to disable.
    type: int
  reassemble_fragments:
    description:
      - When C(yes), specifies that the system reassembles IP fragments.
    type: bool
  receive_window_size:
    description:
      - Specifies the amount of data the BIG-IP system can accept without acknowledging
        the server.
    type: int
  reset_on_timeout:
    description:
      - When C(yes), specifies that the system sends a reset packet (RST) in addition
        to deleting the connection, when a connection exceeds the idle timeout value.
    type: bool
  rtt_from_client:
    description:
      - When C(yes), specifies that the system uses TCP timestamp options to measure
        the round-trip time to the client.
    type: bool
  rtt_from_server:
    description:
      - When C(yes), specifies that the system uses TCP timestamp options to measure
        the round-trip time to the server.
    type: bool
  server_sack:
    description:
      - Specifies whether the BIG-IP system processes Selective ACK (Sack) packets
        in cookie responses from the server.
    type: bool
  server_timestamp:
    description:
      - Specifies whether the BIG-IP system processes timestamp request packets in
        cookie responses from the server.
    type: bool
  syn_cookie_mss:
    description:
      - Specifies a value that overrides the SYN cookie maximum segment size (MSS)
        value in the SYN-ACK packet that is returned to the client.
      - Valid values are 0, and values from 256 through 9162.
    type: int
  tcp_close_timeout:
    description:
      - Specifies the length of time a connection can remain idle before deletion.
    type: str
  tcp_generate_isn:
    description:
      - When C(yes), specifies that the system generates initial sequence numbers
        for SYN packets, according to RFC 1948.
    type: bool
  tcp_handshake_timeout:
    description:
      - Specifies the acceptable duration for a TCP handshake, that is, the maximum
        idle time between a client synchronization (SYN) and a client acknowledgment
        (ACK). If the TCP handshake takes longer than the timeout, the system
        automatically closes the connection.
      - When a number, specifies how long the system can try to establish a TCP
        handshake before timing out.
      - When C(disabled), specifies that the system does not apply a timeout to a
        TCP handshake.
      - When C(indefinite), specifies that attempting a TCP handshake never times out.
    type: str
  tcp_strip_sack:
    description:
      - When C(yes), specifies that the system blocks a TCP selective ACK SackOK
        option from passing to the server on an initiating SYN.
    type: bool
  tcp_time_wait_timeout:
    description:
      - Specifies the number of milliseconds that a connection is in the TIME-WAIT
        state before closing.
    type: int
  tcp_timestamp_mode:
    description:
      - Specifies the action that the system should take on TCP timestamps.
    type: str
    choices:
      - preserve
      - rewrite
      - strip
  tcp_wscale_mode:
    description:
      - Specifies the action that the system should take on TCP windows.
    type: str
    choices:
      - preserve
      - rewrite
      - strip
  timeout_recovery:
    description:
      - Specifies how to handle client-timeout errors for Late Binding.
      - Timeout errors may be caused by a DoS attack or a lossy connection.
      - When C(disconnect), causes the BIG-IP system to drop the connection.
      - When C(fallback), reverts the connection to normal FastL4 load-balancing,
        based on the client's TCP header. This causes the BIG-IP system to choose
        a back-end server based only on the source address and port.
    type: str
    choices:
      - disconnect
      - fallback
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  state:
    description:
      - When C(present), ensures that the profile exists.
      - When C(absent), ensures the profile is removed.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a fastL4 profile
  bigip_profile_fastl4:
    name: foo
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
client_timeout:
  description: The new client timeout value of the resource.
  returned: changed
  type: str
  sample: true
description:
  description: The new description.
  returned: changed
  type: str
  sample: My description
explicit_flow_migration:
  description: The new flow migration setting.
  returned: changed
  type: bool
  sample: yes
idle_timeout:
  description: The new idle timeout setting.
  returned: changed
  type: str
  sample: 123
ip_df_mode:
  description: The new Don't Fragment Flag (DF) setting.
  returned: changed
  type: str
  sample: clear
ip_tos_to_client:
  description: The new IP ToS to Client setting.
  returned: changed
  type: str
  sample: 100
ip_tos_to_server:
  description: The new IP ToS to Server setting.
  returned: changed
  type: str
  sample: 100
ip_ttl_mode:
  description: The new Time To Live (TTL) setting.
  returned: changed
  type: str
  sample: proxy
ip_ttl_v4:
  description: The new Time To Live (TTL) v4 setting.
  returned: changed
  type: int
  sample: 200
ip_ttl_v6:
  description: The new Time To Live (TTL) v6 setting.
  returned: changed
  type: int
  sample: 200
keep_alive_interval:
  description: The new TCP Keep Alive Interval setting.
  returned: changed
  type: int
  sample: 100
late_binding:
  description: The new Late Binding setting.
  returned: changed
  type: bool
  sample: yes
link_qos_to_client:
  description: The new Link QoS to Client setting.
  returned: changed
  type: str
  sample: pass-through
link_qos_to_server:
  description: The new Link QoS to Server setting.
  returned: changed
  type: str
  sample: 123
loose_close:
  description: The new Loose Close setting.
  returned: changed
  type: bool
  sample: no
loose_initialization:
  description: The new Loose Initiation setting.
  returned: changed
  type: bool
  sample: no
mss_override:
  description: The new Maximum Segment Size Override setting.
  returned: changed
  type: int
  sample: 300
reassemble_fragments:
  description: The new Reassemble IP Fragments setting.
  returned: changed
  type: bool
  sample: yes
receive_window_size:
  description: The new Receive Window setting.
  returned: changed
  type: int
  sample: 1024
reset_on_timeout:
  description: The new Reset on Timeout setting.
  returned: changed
  type: bool
  sample: no
rtt_from_client:
  description: The new RTT from Client setting.
  returned: changed
  type: bool
  sample: no
rtt_from_server:
  description: The new RTT from Server setting.
  returned: changed
  type: bool
  sample: no
server_sack:
  description: The new Server Sack setting.
  returned: changed
  type: bool
  sample: yes
server_timestamp:
  description: The new Server Timestamp setting.
  returned: changed
  type: bool
  sample: yes
syn_cookie_mss:
  description: The new SYN Cookie MSS setting.
  returned: changed
  type: int
  sample: 1024
tcp_close_timeout:
  description: The new TCP Close Timeout setting.
  returned: changed
  type: str
  sample: 100
tcp_generate_isn:
  description: The new Generate Initial Sequence Number setting.
  returned: changed
  type: bool
  sample: no
tcp_handshake_timeout:
  description: The new TCP Handshake Timeout setting.
  returned: changed
  type: int
  sample: 5
tcp_strip_sack:
  description: The new Strip Sack OK setting.
  returned: changed
  type: bool
  sample: no
tcp_time_wait_timeout:
  description: The new TCP Time Wait Timeout setting.
  returned: changed
  type: int
  sample: 100
tcp_timestamp_mode:
  description: The new TCP Timestamp Mode setting.
  returned: changed
  type: str
  sample: rewrite
tcp_wscale_mode:
  description: The new TCP Window Scale Mode setting.
  returned: changed
  type: str
  sample: strip
timeout_recovery:
  description: The new Timeout Recovery setting.
  returned: changed
  type: str
  sample: fallback
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import flatten_boolean
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import flatten_boolean


class Parameters(AnsibleF5Parameters):
    api_map = {
        'clientTimeout': 'client_timeout',
        'defaultsFrom': 'parent',
        'explicitFlowMigration': 'explicit_flow_migration',
        'idleTimeout': 'idle_timeout',
        'ipDfMode': 'ip_df_mode',
        'ipTosToClient': 'ip_tos_to_client',
        'ipTosToServer': 'ip_tos_to_server',
        'ipTtlMode': 'ip_ttl_mode',
        'ipTtlV4': 'ip_ttl_v4',
        'ipTtlV6': 'ip_ttl_v6',
        'keepAliveInterval': 'keep_alive_interval',
        'lateBinding': 'late_binding',
        'linkQosToClient': 'link_qos_to_client',
        'linkQosToServer': 'link_qos_to_server',
        'looseClose': 'loose_close',
        'looseInitialization': 'loose_initialization',
        'mssOverride': 'mss_override',
        'reassembleFragments': 'reassemble_fragments',
        'receiveWindowSize': 'receive_window_size',
        'resetOnTimeout': 'reset_on_timeout',
        'rttFromClient': 'rtt_from_client',
        'rttFromServer': 'rtt_from_server',
        'serverSack': 'server_sack',
        'serverTimestamp': 'server_timestamp',
        'synCookieMss': 'syn_cookie_mss',
        'tcpCloseTimeout': 'tcp_close_timeout',
        'tcpGenerateIsn': 'tcp_generate_isn',
        'tcpHandshakeTimeout': 'tcp_handshake_timeout',
        'tcpStripSack': 'tcp_strip_sack',
        'tcpTimeWaitTimeout': 'tcp_time_wait_timeout',
        'tcpTimestampMode': 'tcp_timestamp_mode',
        'tcpWscaleMode': 'tcp_wscale_mode',
        'timeoutRecovery': 'timeout_recovery',
    }

    api_attributes = [
        'clientTimeout',
        'defaultsFrom',
        'description',
        'explicitFlowMigration',
        'idleTimeout',
        'ipDfMode',
        'ipTosToClient',
        'ipTosToServer',
        'ipTtlMode',
        'ipTtlV4',
        'ipTtlV6',
        'keepAliveInterval',
        'lateBinding',
        'linkQosToClient',
        'linkQosToServer',
        'looseClose',
        'looseInitialization',
        'mssOverride',
        'reassembleFragments',
        'receiveWindowSize',
        'resetOnTimeout',
        'rttFromClient',
        'rttFromServer',
        'serverSack',
        'serverTimestamp',
        'synCookieMss',
        'tcpCloseTimeout',
        'tcpGenerateIsn',
        'tcpHandshakeTimeout',
        'tcpStripSack',
        'tcpTimeWaitTimeout',
        'tcpTimestampMode',
        'tcpWscaleMode',
        'timeoutRecovery',
    ]

    returnables = [
        'client_timeout',
        'description',
        'explicit_flow_migration',
        'idle_timeout',
        'ip_df_mode',
        'ip_tos_to_client',
        'ip_tos_to_server',
        'ip_ttl_mode',
        'ip_ttl_v4',
        'ip_ttl_v6',
        'keep_alive_interval',
        'late_binding',
        'link_qos_to_client',
        'link_qos_to_server',
        'loose_close',
        'loose_initialization',
        'mss_override',
        'parent',
        'reassemble_fragments',
        'receive_window_size',
        'reset_on_timeout',
        'rtt_from_client',
        'rtt_from_server',
        'server_sack',
        'server_timestamp',
        'syn_cookie_mss',
        'tcp_close_timeout',
        'tcp_generate_isn',
        'tcp_handshake_timeout',
        'tcp_strip_sack',
        'tcp_time_wait_timeout',
        'tcp_timestamp_mode',
        'tcp_wscale_mode',
        'timeout_recovery',
    ]

    updatables = [
        'client_timeout',
        'description',
        'explicit_flow_migration',
        'idle_timeout',
        'ip_df_mode',
        'ip_tos_to_client',
        'ip_tos_to_server',
        'ip_ttl_mode',
        'ip_ttl_v4',
        'ip_ttl_v6',
        'keep_alive_interval',
        'late_binding',
        'link_qos_to_client',
        'link_qos_to_server',
        'loose_close',
        'loose_initialization',
        'mss_override',
        'parent',
        'reassemble_fragments',
        'receive_window_size',
        'reset_on_timeout',
        'rtt_from_client',
        'rtt_from_server',
        'server_sack',
        'server_timestamp',
        'syn_cookie_mss',
        'tcp_close_timeout',
        'tcp_generate_isn',
        'tcp_handshake_timeout',
        'tcp_strip_sack',
        'tcp_time_wait_timeout',
        'tcp_timestamp_mode',
        'tcp_wscale_mode',
        'timeout_recovery',
    ]

    @property
    def explicit_flow_migration(self):
        result = flatten_boolean(self._values['explicit_flow_migration'])
        return result

    @property
    def late_binding(self):
        return flatten_boolean(self._values['late_binding'])

    @property
    def loose_close(self):
        return flatten_boolean(self._values['loose_close'])

    @property
    def loose_initialization(self):
        return flatten_boolean(self._values['loose_initialization'])

    @property
    def reassemble_fragments(self):
        return flatten_boolean(self._values['reassemble_fragments'])

    @property
    def reset_on_timeout(self):
        return flatten_boolean(self._values['reset_on_timeout'])

    @property
    def rtt_from_client(self):
        return flatten_boolean(self._values['rtt_from_client'])

    @property
    def rtt_from_server(self):
        return flatten_boolean(self._values['rtt_from_server'])

    @property
    def server_sack(self):
        return flatten_boolean(self._values['server_sack'])

    @property
    def server_timestamp(self):
        return flatten_boolean(self._values['server_timestamp'])

    @property
    def tcp_generate_isn(self):
        return flatten_boolean(self._values['tcp_generate_isn'])

    @property
    def tcp_strip_sack(self):
        return flatten_boolean(self._values['tcp_strip_sack'])

    @property
    def tcp_close_timeout(self):
        if self._values['tcp_close_timeout'] is None:
            return None
        try:
            return int(self._values['tcp_close_timeout'])
        except ValueError:
            return self._values['tcp_close_timeout']

    @property
    def tcp_handshake_timeout(self):
        if self._values['tcp_handshake_timeout'] is None:
            return None
        try:
            return int(self._values['tcp_handshake_timeout'])
        except ValueError:
            if self._values['tcp_handshake_timeout'] in ['disabled', 'immediate']:
                return 0
            return self._values['tcp_handshake_timeout']

    @property
    def client_timeout(self):
        if self._values['client_timeout'] is None:
            return None
        try:
            return int(self._values['client_timeout'])
        except ValueError:
            if self._values['client_timeout'] == 'immediate':
                return 0
            if self._values['client_timeout'] == 'indefinite':
                return 4294967295
            return self._values['client_timeout']

    @property
    def parent(self):
        if self._values['parent'] is None:
            return None
        result = fq_name(self.partition, self._values['parent'])
        return result


class ApiParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

    @property
    def idle_timeout(self):
        if self._values['idle_timeout'] is None:
            return None
        try:
            return int(self._values['idle_timeout'])
        except ValueError:
            return self._values['idle_timeout']

    @property
    def ip_tos_to_client(self):
        return self.transform_ip_tos('ip_tos_to_client')

    @property
    def ip_tos_to_server(self):
        return self.transform_ip_tos('ip_tos_to_server')

    @property
    def keep_alive_interval(self):
        if self._values['keep_alive_interval'] is None:
            return None
        try:
            return int(self._values['keep_alive_interval'])
        except ValueError:
            return self._values['keep_alive_interval']

    @property
    def link_qos_to_client(self):
        return self.transform_link_qos('link_qos_to_client')

    @property
    def link_qos_to_server(self):
        return self.transform_link_qos('link_qos_to_server')

    def transform_ip_tos(self, key):
        if self._values[key] is None:
            return None
        try:
            result = int(self._values[key])
            return result
        except ValueError:
            return self._values[key]

    def transform_link_qos(self, key):
        if self._values[key] is None:
            return None
        if self._values[key] == 'pass-through':
            return 'pass-through'
        if 0 <= int(self._values[key]) <= 7:
            return int(self._values[key])


class ModuleParameters(Parameters):
    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']

    @property
    def idle_timeout(self):
        if self._values['idle_timeout'] is None:
            return None
        try:
            result = int(self._values['idle_timeout'])
            if result == 0:
                return 'immediate'
            return result
        except ValueError:
            return self._values['idle_timeout']

    @property
    def ip_tos_to_client(self):
        return self.transform_ip_tos('ip_tos_to_client')

    @property
    def ip_tos_to_server(self):
        return self.transform_ip_tos('ip_tos_to_server')

    @property
    def ip_ttl_v4(self):
        if self._values['ip_ttl_v4'] is None:
            return None
        if 0 <= self._values['ip_ttl_v4'] <= 255:
            return int(self._values['ip_ttl_v4'])
        raise F5ModuleError(
            'ip_ttl_v4 must be between 0 and 255'
        )

    @property
    def ip_ttl_v6(self):
        if self._values['ip_ttl_v6'] is None:
            return None
        if 0 <= self._values['ip_ttl_v6'] <= 255:
            return int(self._values['ip_ttl_v6'])
        raise F5ModuleError(
            'ip_ttl_v6 must be between 0 and 255'
        )

    @property
    def keep_alive_interval(self):
        if self._values['keep_alive_interval'] is None:
            return None
        result = int(self._values['keep_alive_interval'])
        if result == 0:
            return 'disabled'
        return result

    @property
    def link_qos_to_client(self):
        result = self.transform_link_qos('link_qos_to_client')
        if result == -1:
            raise F5ModuleError(
                'link_qos_to_client must be between 0 and 7'
            )
        return result

    @property
    def link_qos_to_server(self):
        result = self.transform_link_qos('link_qos_to_server')
        if result == -1:
            raise F5ModuleError(
                'link_qos_to_server must be between 0 and 7'
            )
        return result

    def transform_link_qos(self, key):
        if self._values[key] is None:
            return None
        if self._values[key] == 'pass-through':
            return 'pass-through'
        if 0 <= int(self._values[key]) <= 7:
            return int(self._values[key])
        else:
            return -1

    def transform_ip_tos(self, key):
        if self._values[key] is None:
            return None
        try:
            result = int(self._values[key])
            return result
        except ValueError:
            if self._values[key] == 'mimic':
                return 65534
            return self._values[key]


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def explicit_flow_migration(self):
        if self._values['explicit_flow_migration'] == 'yes':
            return 'enabled'
        elif self._values['explicit_flow_migration'] == 'no':
            return 'disabled'

    @property
    def late_binding(self):
        if self._values['late_binding'] == 'yes':
            return 'enabled'
        elif self._values['late_binding'] == 'no':
            return 'disabled'

    @property
    def loose_close(self):
        if self._values['loose_close'] == 'yes':
            return 'enabled'
        elif self._values['loose_close'] == 'no':
            return 'disabled'

    @property
    def loose_initialization(self):
        if self._values['loose_initialization'] == 'yes':
            return 'enabled'
        elif self._values['loose_initialization'] == 'no':
            return 'disabled'

    @property
    def reassemble_fragments(self):
        if self._values['reassemble_fragments'] == 'yes':
            return 'enabled'
        elif self._values['reassemble_fragments'] == 'no':
            return 'disabled'

    @property
    def reset_on_timeout(self):
        if self._values['reset_on_timeout'] == 'yes':
            return 'enabled'
        elif self._values['reset_on_timeout'] == 'no':
            return 'disabled'

    @property
    def rtt_from_client(self):
        if self._values['rtt_from_client'] == 'yes':
            return 'enabled'
        elif self._values['rtt_from_client'] == 'no':
            return 'disabled'

    @property
    def rtt_from_server(self):
        if self._values['rtt_from_server'] == 'yes':
            return 'enabled'
        elif self._values['rtt_from_server'] == 'no':
            return 'disabled'

    @property
    def server_sack(self):
        if self._values['server_sack'] == 'yes':
            return 'enabled'
        elif self._values['server_sack'] == 'no':
            return 'disabled'

    @property
    def server_timestamp(self):
        if self._values['server_timestamp'] == 'yes':
            return 'enabled'
        elif self._values['server_timestamp'] == 'no':
            return 'disabled'

    @property
    def tcp_generate_isn(self):
        if self._values['tcp_generate_isn'] == 'yes':
            return 'enabled'
        elif self._values['tcp_generate_isn'] == 'no':
            return 'disabled'

    @property
    def tcp_strip_sack(self):
        if self._values['tcp_strip_sack'] == 'yes':
            return 'enabled'
        elif self._values['tcp_strip_sack'] == 'no':
            return 'disabled'


class ReportableChanges(Changes):
    @property
    def explicit_flow_migration(self):
        result = flatten_boolean(self._values['explicit_flow_migration'])
        return result

    @property
    def late_binding(self):
        result = flatten_boolean(self._values['late_binding'])
        return result

    @property
    def loose_close(self):
        result = flatten_boolean(self._values['loose_close'])
        return result

    @property
    def loose_initialization(self):
        result = flatten_boolean(self._values['loose_initialization'])
        return result

    @property
    def reassemble_fragments(self):
        result = flatten_boolean(self._values['reassemble_fragments'])
        return result

    @property
    def reset_on_timeout(self):
        result = flatten_boolean(self._values['reset_on_timeout'])
        return result

    @property
    def rtt_from_client(self):
        result = flatten_boolean(self._values['rtt_from_client'])
        return result

    @property
    def rtt_from_server(self):
        result = flatten_boolean(self._values['rtt_from_server'])
        return result

    @property
    def server_sack(self):
        result = flatten_boolean(self._values['server_sack'])
        return result

    @property
    def server_timestamp(self):
        result = flatten_boolean(self._values['server_timestamp'])
        return result

    @property
    def tcp_generate_isn(self):
        result = flatten_boolean(self._values['tcp_generate_isn'])
        return result

    @property
    def tcp_strip_sack(self):
        result = flatten_boolean(self._values['tcp_strip_sack'])
        return result

    @property
    def ip_tos_to_client(self):
        return self.report_ip_tos('ip_tos_to_client')

    @property
    def ip_tos_to_server(self):
        return self.report_ip_tos('ip_tos_to_server')

    @property
    def keep_alive_interval(self):
        if self._values['keep_alive_interval'] is None:
            return None
        if self._values['keep_alive_interval'] == 'disabled':
            return 0
        return self._values['keep_alive_interval']

    @property
    def client_timeout(self):
        if self._values['client_timeout'] is None:
            return None
        try:
            return int(self._values['client_timeout'])
        except ValueError:
            if self._values['client_timeout'] == 0:
                return 'immediate'
            if self._values['client_timeout'] == 4294967295:
                return 'indefinite'
            return self._values['client_timeout']

    def report_ip_tos(self, key):
        if self._values[key] is None:
            return None
        if self._values[key] == 65534:
            return 'mimic'
        try:
            return int(self._values[key])
        except ValueError:
            return self._values[key]


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def parent(self):
        if self.want.parent != self.have.parent:
            raise F5ModuleError(
                "The parent profile cannot be changed"
            )

    @property
    def description(self):
        if self.want.description is None:
            return None
        if self.have.description is None and self.want.description == '':
            return None
        if self.want.description != self.have.description:
            return self.want.description


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            parent=dict(),
            idle_timeout=dict(),
            client_timeout=dict(),
            description=dict(),
            explicit_flow_migration=dict(type='bool'),
            ip_df_mode=dict(
                choices=['pmtu', 'preserve', 'set', 'clear']
            ),
            ip_tos_to_client=dict(),
            ip_tos_to_server=dict(),
            ip_ttl_v4=dict(type='int'),
            ip_ttl_v6=dict(type='int'),
            ip_ttl_mode=dict(
                choices=['proxy', 'set', 'preserve', 'decrement']
            ),
            keep_alive_interval=dict(type='int'),
            late_binding=dict(type='bool'),
            link_qos_to_client=dict(),
            link_qos_to_server=dict(),
            loose_close=dict(type='bool'),
            loose_initialization=dict(type='bool'),
            mss_override=dict(type='int'),
            reassemble_fragments=dict(type='bool'),
            receive_window_size=dict(type='int'),
            reset_on_timeout=dict(type='bool'),
            rtt_from_client=dict(type='bool'),
            rtt_from_server=dict(type='bool'),
            server_sack=dict(type='bool'),
            server_timestamp=dict(type='bool'),
            syn_cookie_mss=dict(type='int'),
            tcp_close_timeout=dict(),
            tcp_generate_isn=dict(type='bool'),
            tcp_handshake_timeout=dict(),
            tcp_strip_sack=dict(type='bool'),
            tcp_time_wait_timeout=dict(type='int'),
            tcp_timestamp_mode=dict(
                choices=['preserve', 'rewrite', 'strip']
            ),
            tcp_wscale_mode=dict(
                choices=['preserve', 'rewrite', 'strip']
            ),
            timeout_recovery=dict(
                choices=['fallback', 'disconnect']
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
