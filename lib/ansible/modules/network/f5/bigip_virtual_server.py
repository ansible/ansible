#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_virtual_server
short_description: Manage LTM virtual servers on a BIG-IP
description:
  - Manage LTM virtual servers on a BIG-IP.
version_added: 2.1
options:
  state:
    description:
      - The virtual server state. If C(absent), delete the virtual server
        if it exists. C(present) creates the virtual server and enable it.
        If C(enabled), enable the virtual server if it exists. If C(disabled),
        create the virtual server if needed, and set state to C(disabled).
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
  type:
    description:
      - Specifies the network service provided by this virtual server.
      - When creating a new virtual server, if this parameter is not provided, the
        default will be C(standard).
      - This value cannot be changed after it is set.
      - When C(standard), specifies a virtual server that directs client traffic to
        a load balancing pool and is the most basic type of virtual server. When you
        first create the virtual server, you assign an existing default pool to it.
        From then on, the virtual server automatically directs traffic to that default pool.
      - When C(forwarding-l2), specifies a virtual server that shares the same IP address as a
        node in an associated VLAN.
      - When C(forwarding-ip), specifies a virtual server like other virtual servers, except
        that the virtual server has no pool members to load balance. The virtual server simply
        forwards the packet directly to the destination IP address specified in the client request.
      - When C(performance-http), specifies a virtual server with which you associate a Fast HTTP
        profile. Together, the virtual server and profile increase the speed at which the virtual
        server processes HTTP requests.
      - When C(performance-l4), specifies a virtual server with which you associate a Fast L4 profile.
        Together, the virtual server and profile increase the speed at which the virtual server
        processes layer 4 requests.
      - When C(stateless), specifies a virtual server that accepts traffic matching the virtual
        server address and load balances the packet to the pool members without attempting to
        match the packet to a pre-existing connection in the connection table. New connections
        are immediately removed from the connection table. This addresses the requirement for
        one-way UDP traffic that needs to be processed at very high throughput levels, for example,
        load balancing syslog traffic to a pool of syslog servers. Stateless virtual servers are
        not suitable for processing traffic that requires stateful tracking, such as TCP traffic.
        Stateless virtual servers do not support iRules, persistence, connection mirroring,
        rateshaping, or SNAT automap.
      - When C(reject), specifies that the BIG-IP system rejects any traffic destined for the
        virtual server IP address.
      - When C(dhcp), specifies a virtual server that relays Dynamic Host Control Protocol (DHCP)
        client requests for an IP address to one or more DHCP servers, and provides DHCP server
        responses with an available IP address for the client.
      - When C(internal), specifies a virtual server that supports modification of HTTP requests
        and responses. Internal virtual servers enable usage of ICAP (Internet Content Adaptation
        Protocol) servers to modify HTTP requests and responses by creating and applying an ICAP
        profile and adding Request Adapt or Response Adapt profiles to the virtual server.
      - When C(message-routing), specifies a virtual server that uses a SIP application protocol
        and functions in accordance with a SIP session profile and SIP router profile.
    choices:
      - standard
      - forwarding-l2
      - forwarding-ip
      - performance-http
      - performance-l4
      - stateless
      - reject
      - dhcp
      - internal
      - message-routing
    default: standard
    version_added: 2.6
  name:
    description:
      - Virtual server name.
    required: True
    aliases:
      - vs
  destination:
    description:
      - Destination IP of the virtual server.
      - Required when C(state) is C(present) and virtual server does not exist.
      - When C(type) is C(internal), this parameter is ignored. For all other types,
        it is required.
    aliases:
      - address
      - ip
  source:
    description:
      - Specifies an IP address or network from which the virtual server accepts traffic.
      - The virtual server accepts clients only from one of these IP addresses.
      - For this setting to function effectively, specify a value other than 0.0.0.0/0 or ::/0
        (that is, any/0, any6/0).
      - In order to maximize utility of this setting, specify the most specific address
        prefixes covering all customer addresses and no others.
      - Specify the IP address in Classless Inter-Domain Routing (CIDR) format; address/prefix,
        where the prefix length is in bits. For example, for IPv4, 10.0.0.1/32 or 10.0.0.0/24,
        and for IPv6, ffe1::0020/64 or 2001:ed8:77b5:2:10:10:100:42/64.
    version_added: 2.5
  port:
    description:
      - Port of the virtual server. Required when C(state) is C(present)
        and virtual server does not exist.
      - If you do not want to specify a particular port, use the value C(0).
        The result is that the virtual server will listen on any port.
      - When C(type) is C(dhcp), this module will force the C(port) parameter to be C(67).
      - When C(type) is C(internal), this module will force the C(port) parameter to be C(0).
      - In addition to specifying a port number, a select number of service names may also
        be provided.
      - The string C(ftp) may be substituted for for port C(21).
      - The string C(http) may be substituted for for port C(80).
      - The string C(https) may be substituted for for port C(443).
      - The string C(telnet) may be substituted for for port C(23).
      - The string C(smtp) may be substituted for for port C(25).
      - The string C(snmp) may be substituted for for port C(161).
      - The string C(snmp-trap) may be substituted for for port C(162).
      - The string C(ssh) may be substituted for for port C(22).
      - The string C(tftp) may be substituted for for port C(69).
      - The string C(isakmp) may be substituted for for port C(500).
      - The string C(mqtt) may be substituted for for port C(1883).
      - The string C(mqtt-tls) may be substituted for for port C(8883).
  profiles:
    description:
      - List of profiles (HTTP, ClientSSL, ServerSSL, etc) to apply to both sides
        of the connection (client-side and server-side).
      - If you only want to apply a particular profile to the client-side of
        the connection, specify C(client-side) for the profile's C(context).
      - If you only want to apply a particular profile to the server-side of
        the connection, specify C(server-side) for the profile's C(context).
      - If C(context) is not provided, it will default to C(all).
      - If you want to remove a profile from the list of profiles currently active
        on the virtual, then simply remove it from the C(profiles) list. See
        examples for an illustration of this.
      - If you want to add a profile to the list of profiles currently active
        on the virtual, then simply add it to the C(profiles) list. See
        examples for an illustration of this.
      - B(Profiles matter). There is a good chance that this module will fail to configure
        a BIG-IP if you mix up your profiles, or, if you attempt to set an IP protocol
        which your current, or new, profiles do not support. Both this module, and BIG-IP,
        will tell you when you are wrong, with an error resembling C(lists profiles
        incompatible with its protocol).
      - If you are unsure what correct profile combinations are, then have a BIG-IP
        available to you in which you can make changes and copy what the correct
        combinations are.
    suboptions:
      name:
        description:
          - Name of the profile.
          - If this is not specified, then it is assumed that the profile item is
            only a name of a profile.
          - This must be specified if a context is specified.
      context:
        description:
          - The side of the connection on which the profile should be applied.
        choices:
          - all
          - server-side
          - client-side
        default: all
    aliases:
      - all_profiles
  irules:
    version_added: 2.2
    description:
      - List of rules to be applied in priority order.
      - If you want to remove existing iRules, specify a single empty value; C("").
        See the documentation for an example.
      - When C(type) is C(dhcp), this parameter will be ignored.
      - When C(type) is C(stateless), this parameter will be ignored.
      - When C(type) is C(reject), this parameter will be ignored.
      - When C(type) is C(internal), this parameter will be ignored.
    aliases:
      - all_rules
  enabled_vlans:
    version_added: "2.2"
    description:
      - List of VLANs to be enabled. When a VLAN named C(all) is used, all
        VLANs will be allowed. VLANs can be specified with or without the
        leading partition. If the partition is not specified in the VLAN,
        then the C(partition) option of this module will be used.
      - This parameter is mutually exclusive with the C(disabled_vlans) parameter.
  disabled_vlans:
    version_added: 2.5
    description:
      - List of VLANs to be disabled. If the partition is not specified in the VLAN,
        then the C(partition) option of this module will be used.
      - This parameter is mutually exclusive with the C(enabled_vlans) parameters.
  pool:
    description:
      - Default pool for the virtual server.
      - If you want to remove the existing pool, specify an empty value; C("").
        See the documentation for an example.
      - When creating a new virtual server, and C(type) is C(stateless), this parameter
        is required.
      - If C(type) is C(stateless), the C(pool) that is used must not have any members
        which define a C(rate_limit).
  policies:
    description:
      - Specifies the policies for the virtual server.
      - When C(type) is C(dhcp), this parameter will be ignored.
      - When C(type) is C(reject), this parameter will be ignored.
      - When C(type) is C(internal), this parameter will be ignored.
    aliases:
      - all_policies
  snat:
    description:
      - Source network address policy.
      - When C(type) is C(dhcp), this parameter is ignored.
      - When C(type) is C(reject), this parameter will be ignored.
      - When C(type) is C(internal), this parameter will be ignored.
      - The name of a SNAT pool (eg "/Common/snat_pool_name") can be specified to enable SNAT
        with the specific pool.
      - To remove SNAT, specify the word C(none).
      - To specify automap, use the word C(automap).
  default_persistence_profile:
    description:
      - Default Profile which manages the session persistence.
      - If you want to remove the existing default persistence profile, specify an
        empty value; C(""). See the documentation for an example.
      - When C(type) is C(dhcp), this parameter will be ignored.
  description:
    description:
      - Virtual server description.
  fallback_persistence_profile:
    description:
      - Specifies the persistence profile you want the system to use if it
        cannot use the specified default persistence profile.
      - If you want to remove the existing fallback persistence profile, specify an
        empty value; C(""). See the documentation for an example.
      - When C(type) is C(dhcp), this parameter will be ignored.
    version_added: 2.3
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  metadata:
    description:
      - Arbitrary key/value pairs that you can attach to a pool. This is useful in
        situations where you might want to annotate a virtual to me managed by Ansible.
      - Key names will be stored as strings; this includes names that are numbers.
      - Values for all of the keys will be stored as strings; this includes values
        that are numbers.
      - Data will be persisted, not ephemeral.
    version_added: 2.5
  address_translation:
    description:
      - Specifies, when C(enabled), that the system translates the address of the
        virtual server.
      - When C(disabled), specifies that the system uses the address without translation.
      - This option is useful when the system is load balancing devices that have the
        same IP address.
      - When creating a new virtual server, the default is C(enabled).
    type: bool
    version_added: 2.6
  port_translation:
    description:
      - Specifies, when C(enabled), that the system translates the port of the virtual
        server.
      - When C(disabled), specifies that the system uses the port without translation.
        Turning off port translation for a virtual server is useful if you want to use
        the virtual server to load balance connections to any service.
      - When creating a new virtual server, the default is C(enabled).
    type: bool
    version_added: 2.6
  ip_protocol:
    description:
      - Specifies a network protocol name you want the system to use to direct traffic
        on this virtual server.
      - When creating a new virtual server, if this parameter is not specified, the default is C(tcp).
      - The Protocol setting is not available when you select Performance (HTTP) as the Type.
      - The value of this argument can be specified in either it's numeric value, or,
        for convenience, in a select number of named values. Refer to C(choices) for examples.
      - For a list of valid IP protocol numbers, refer to this page
        https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers
      - When C(type) is C(dhcp), this module will force the C(ip_protocol) parameter to be C(17) (UDP).
    choices:
      - ah
      - bna
      - esp
      - etherip
      - gre
      - icmp
      - ipencap
      - ipv6
      - ipv6-auth
      - ipv6-crypt
      - ipv6-icmp
      - isp-ip
      - mux
      - ospf
      - sctp
      - tcp
      - udp
      - udplite
    version_added: 2.6
  firewall_enforced_policy:
    description:
      - Applies the specify AFM policy to the virtual in an enforcing way.
      - When creating a new virtual, if this parameter is not specified, the enforced
        policy is disabled.
    version_added: 2.6
  firewall_staged_policy:
    description:
      - Applies the specify AFM policy to the virtual in an enforcing way.
      - A staged policy shows the results of the policy rules in the log, while not
        actually applying the rules to traffic.
      - When creating a new virtual, if this parameter is not specified, the staged
        policy is disabled.
    version_added: 2.6
  security_log_profiles:
    description:
      - Specifies the log profile applied to the virtual server.
      - To make use of this feature, the AFM module must be licensed and provisioned.
      - The C(Log all requests) and C(Log illegal requests) are mutually exclusive and
        therefore, this module will raise an error if the two are specified together.
    version_added: 2.6
notes:
  - Requires BIG-IP software version >= 11
  - Requires the netaddr Python package on the host. This is as easy as pip
    install netaddr.
requirements:
  - netaddr
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Modify Port of the Virtual Server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    state: present
    partition: Common
    name: my-virtual-server
    port: 8080
  delegate_to: localhost

- name: Delete virtual server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    state: absent
    partition: Common
    name: my-virtual-server
  delegate_to: localhost

- name: Add virtual server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    state: present
    partition: Common
    name: my-virtual-server
    destination: 10.10.10.10
    port: 443
    pool: my-pool
    snat: Automap
    description: Test Virtual Server
    profiles:
      - http
      - fix
      - name: clientssl
        context: server-side
      - name: ilx
        context: client-side
    policies:
      - my-ltm-policy-for-asm
      - ltm-uri-policy
      - ltm-policy-2
      - ltm-policy-3
    enabled_vlans:
      - /Common/vlan2
  delegate_to: localhost

- name: Add FastL4 virtual server
  bigip_virtual_server:
    destination: 1.1.1.1
    name: fastl4_vs
    port: 80
    profiles:
      - fastL4
    state: present

- name: Add iRules to the Virtual Server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    name: my-virtual-server
    irules:
      - irule1
      - irule2
  delegate_to: localhost

- name: Remove one iRule from the Virtual Server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    name: my-virtual-server
    irules:
      - irule2
  delegate_to: localhost

- name: Remove all iRules from the Virtual Server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    name: my-virtual-server
    irules: ""
  delegate_to: localhost

- name: Remove pool from the Virtual Server
  bigip_virtual_server:
    server: lb.mydomain.net
    user: admin
    password: secret
    name: my-virtual-server
    pool: ""
  delegate_to: localhost

- name: Add metadata to virtual
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    name: my-pool
    partition: Common
    metadata:
      ansible: 2.4
      updated_at: 2017-12-20T17:50:46Z
  delegate_to: localhost

- name: Add virtual with two profiles
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    name: my-pool
    partition: Common
    profiles:
      - http
      - tcp
  delegate_to: localhost

- name: Remove HTTP profile from previous virtual
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    name: my-pool
    partition: Common
    profiles:
      - tcp
  delegate_to: localhost

- name: Add the HTTP profile back to the previous virtual
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    name: my-pool
    partition: Common
    profiles:
      - http
      - tcp
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: New description of the virtual server.
  returned: changed
  type: string
  sample: This is my description
default_persistence_profile:
  description: Default persistence profile set on the virtual server.
  returned: changed
  type: string
  sample: /Common/dest_addr
destination:
  description: Destination of the virtual server.
  returned: changed
  type: string
  sample: 1.1.1.1
disabled:
  description: Whether the virtual server is disabled, or not.
  returned: changed
  type: bool
  sample: True
disabled_vlans:
  description: List of VLANs that the virtual is disabled for.
  returned: changed
  type: list
  sample: ['/Common/vlan1', '/Common/vlan2']
enabled:
  description: Whether the virtual server is enabled, or not.
  returned: changed
  type: bool
  sample: False
enabled_vlans:
  description: List of VLANs that the virtual is enabled for.
  returned: changed
  type: list
  sample: ['/Common/vlan5', '/Common/vlan6']
fallback_persistence_profile:
  description: Fallback persistence profile set on the virtual server.
  returned: changed
  type: string
  sample: /Common/source_addr
irules:
  description: iRules set on the virtual server.
  returned: changed
  type: list
  sample: ['/Common/irule1', '/Common/irule2']
pool:
  description: Pool that the virtual server is attached to.
  returned: changed
  type: string
  sample: /Common/my-pool
policies:
  description: List of policies attached to the virtual.
  returned: changed
  type: list
  sample: ['/Common/policy1', '/Common/policy2']
port:
  description: Port that the virtual server is configured to listen on.
  returned: changed
  type: int
  sample: 80
profiles:
  description: List of profiles set on the virtual server.
  returned: changed
  type: list
  sample: [{'name': 'tcp', 'context': 'server-side'}, {'name': 'tcp-legacy', 'context': 'client-side'}]
snat:
  description: SNAT setting of the virtual server.
  returned: changed
  type: string
  sample: Automap
source:
  description: Source address, in CIDR form, set on the virtual server.
  returned: changed
  type: string
  sample: 1.2.3.4/32
metadata:
  description: The new value of the virtual.
  returned: changed
  type: dict
  sample: {'key1': 'foo', 'key2': 'bar'}
address_translation:
  description: The new value specifying whether address translation is on or off.
  returned: changed
  type: bool
  sample: True
port_translation:
  description: The new value specifying whether port translation is on or off.
  returned: changed
  type: bool
  sample: True
ip_protocol:
  description: The new value of the IP protocol.
  returned: changed
  type: int
  sample: 6
firewall_enforced_policy:
  description: The new enforcing firewall policy.
  returned: changed
  type: string
  sample: /Common/my-enforced-fw
firewall_staged_policy:
  description: The new staging firewall policy.
  returned: changed
  type: string
  sample: /Common/my-staged-fw
security_log_profiles:
  description: The new list of security log profiles.
  returned: changed
  type: list
  sample: ['/Common/profile1', '/Common/profile2']
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems
from collections import namedtuple

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False

try:
    import netaddr
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'sourceAddressTranslation': 'snat',
        'fallbackPersistence': 'fallback_persistence_profile',
        'persist': 'default_persistence_profile',
        'vlansEnabled': 'vlans_enabled',
        'vlansDisabled': 'vlans_disabled',
        'profilesReference': 'profiles',
        'policiesReference': 'policies',
        'rules': 'irules',
        'translateAddress': 'address_translation',
        'translatePort': 'port_translation',
        'ipProtocol': 'ip_protocol',
        'fwEnforcedPolicy': 'firewall_enforced_policy',
        'fwStagedPolicy': 'firewall_staged_policy',
        'securityLogProfiles': 'security_log_profiles'
    }

    api_attributes = [
        'description',
        'destination',
        'disabled',
        'enabled',
        'fallbackPersistence',
        # 'ipProtocol',
        'metadata',
        'persist',
        'policies',
        'pool',
        'profiles',
        'rules',
        'source',
        'sourceAddressTranslation',
        'vlans',
        'vlansEnabled',
        'vlansDisabled',
        'translateAddress',
        'translatePort',
        'l2Forward',
        'ipForward',
        'stateless',
        'reject',
        'dhcpRelay',
        'internal',
        'fwEnforcedPolicy',
        'fwStagedPolicy',
        'securityLogProfiles',
    ]

    updatables = [
        'address_translation',
        'description',
        'default_persistence_profile',
        'destination',
        'disabled_vlans',
        'enabled',
        'enabled_vlans',
        'fallback_persistence_profile',
        # 'ip_protocol',
        'irules',
        'metadata',
        'pool',
        'policies',
        'port',
        'port_translation',
        'profiles',
        'snat',
        'source',
        'type',
        'firewall_enforced_policy',
        'firewall_staged_policy',
        'security_log_profiles',
    ]

    returnables = [
        'address_translation',
        'description',
        'default_persistence_profile',
        'destination',
        'disabled',
        'disabled_vlans',
        'enabled',
        'enabled_vlans',
        'fallback_persistence_profile',
        # 'ip_protocol',
        'irules',
        'metadata',
        'pool',
        'policies',
        'port',
        'port_translation',
        'profiles',
        'snat',
        'source',
        'vlans',
        'vlans_enabled',
        'vlans_disabled',
        'type',
        'firewall_enforced_policy',
        'firewall_staged_policy',
        'security_log_profiles',
    ]

    profiles_mutex = [
        'sip', 'sipsession', 'iiop', 'rtsp', 'http', 'diameter',
        'diametersession', 'radius', 'ftp', 'tftp', 'dns', 'pptp', 'fix'
    ]

    ip_protocols_map = [
        ('ah', 51),
        ('bna', 49),
        ('esp', 50),
        ('etherip', 97),
        ('gre', 47),
        ('icmp', 1),
        ('ipencap', 4),
        ('ipv6', 41),
        ('ipv6-auth', 51),   # not in the official list
        ('ipv6-crypt', 50),  # not in the official list
        ('ipv6-icmp', 58),
        ('iso-ip', 80),
        ('mux', 18),
        ('ospf', 89),
        ('sctp', 132),
        ('tcp', 6),
        ('udp', 17),
        ('udplite', 136),
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            try:
                result[returnable] = getattr(self, returnable)
            except Exception:
                pass
        result = self._filter_params(result)
        return result

    def is_valid_ip(self, value):
        try:
            netaddr.IPAddress(value)
            return True
        except (netaddr.core.AddrFormatError, ValueError):
            return False

    def _format_port_for_destination(self, ip, port):
        addr = netaddr.IPAddress(ip)
        if addr.version == 6:
            if port == 0:
                result = '.any'
            else:
                result = '.{0}'.format(port)
        else:
            result = ':{0}'.format(port)
        return result

    def _format_destination(self, address, port, route_domain):
        if port is None:
            if route_domain is None:
                result = '{0}'.format(
                    fq_name(self.partition, address)
                )
            else:
                result = '{0}%{1}'.format(
                    fq_name(self.partition, address),
                    route_domain
                )
        else:
            port = self._format_port_for_destination(address, port)
            if route_domain is None:
                result = '{0}{1}'.format(
                    fq_name(self.partition, address),
                    port
                )
            else:
                result = '{0}%{1}{2}'.format(
                    fq_name(self.partition, address),
                    route_domain,
                    port
                )
        return result

    @property
    def ip_protocol(self):
        if self._values['ip_protocol'] is None:
            return None
        if self._values['ip_protocol'] == 'any':
            return 'any'
        for x in self.ip_protocols_map:
            if x[0] == self._values['ip_protocol']:
                return int(x[1])
        try:
            return int(self._values['ip_protocol'])
        except ValueError:
            raise F5ModuleError(
                "Specified ip_protocol was neither a number nor in the list of common protocols."
            )

    @property
    def has_message_routing_profiles(self):
        if self.profiles is None:
            return None
        current = self._read_current_message_routing_profiles_from_device()
        result = [x['name'] for x in self.profiles if x['name'] in current]
        if len(result) > 0:
            return True
        return False

    @property
    def has_fastl4_profiles(self):
        if self.profiles is None:
            return None
        current = self._read_current_fastl4_profiles_from_device()
        result = [x['name'] for x in self.profiles if x['name'] in current]
        if len(result) > 0:
            return True
        return False

    @property
    def has_fasthttp_profiles(self):
        """Check if ``fasthttp`` profile is in API profiles

        This method is used to determine the server type when doing comparisons
        in the Difference class.

        Returns:
             bool: True if server has ``fasthttp`` profiles. False otherwise.
        """
        if self.profiles is None:
            return None
        current = self._read_current_fasthttp_profiles_from_device()
        result = [x['name'] for x in self.profiles if x['name'] in current]
        if len(result) > 0:
            return True
        return False

    def _read_current_message_routing_profiles_from_device(self):
        collection1 = self.client.api.tm.ltm.profile.diameters.get_collection()
        collection2 = self.client.api.tm.ltm.profile.sips.get_collection()
        result = [x.name for x in collection1]
        result += [x.name for x in collection2]
        return result

    def _read_current_fastl4_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.fastl4s.get_collection()
        result = [x.name for x in collection]
        return result

    def _read_current_fasthttp_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.fasthttps.get_collection()
        result = [x.name for x in collection]
        return result


class ApiParameters(Parameters):
    @property
    def type(self):
        """Attempt to determine the current server type

        This check is very unscientific. It turns out that this information is not
        exactly available anywhere on a BIG-IP. Instead, we rely on a semi-reliable
        means for determining what the type of the virtual server is. Hopefully it
        always works.

        There are a handful of attributes that can be used to determine a specific
        type. There are some types though that can only be determined by looking at
        the profiles that are assigned to them. We follow that method for those
        complicated types; message-routing, fasthttp, and fastl4.

        Because type determination is an expensive operation, we cache the result
        from the operation.

        Returns:
            string: The server type.
        """
        if self._values['type']:
            return self._values['type']
        if self.l2Forward is True:
            result = 'forwarding-l2'
        elif self.ipForward is True:
            result = 'forwarding-ip'
        elif self.stateless is True:
            result = 'stateless'
        elif self.reject is True:
            result = 'reject'
        elif self.dhcpRelay is True:
            result = 'dhcp'
        elif self.internal is True:
            result = 'internal'
        elif self.has_fasthttp_profiles:
            result = 'performance-http'
        elif self.has_fastl4_profiles:
            result = 'performance-l4'
        elif self.has_message_routing_profiles:
            result = 'message-routing'
        else:
            result = 'standard'
        self._values['type'] = result
        return result

    @property
    def destination(self):
        if self._values['destination'] is None:
            return None
        destination = self.destination_tuple
        result = self._format_destination(destination.ip, destination.port, destination.route_domain)
        return result

    @property
    def source(self):
        if self._values['source'] is None:
            return None
        try:
            addr = netaddr.IPNetwork(self._values['source'])
            result = '{0}/{1}'.format(str(addr.ip), addr.prefixlen)
            return result
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The source IP address must be specified in CIDR format: address/prefix"
            )

    @property
    def destination_tuple(self):
        Destination = namedtuple('Destination', ['ip', 'port', 'route_domain'])

        # Remove the partition
        if self._values['destination'] is None:
            result = Destination(ip=None, port=None, route_domain=None)
            return result
        destination = re.sub(r'^/[a-zA-Z0-9_.-]+/', '', self._values['destination'])

        if self.is_valid_ip(destination):
            result = Destination(
                ip=destination,
                port=None,
                route_domain=None
            )
            return result

        # Covers the following examples
        #
        # /Common/2700:bc00:1f10:101::6%2.80
        # 2700:bc00:1f10:101::6%2.80
        # 1.1.1.1%2:80
        # /Common/1.1.1.1%2:80
        # /Common/2700:bc00:1f10:101::6%2.any
        #
        pattern = r'(?P<ip>[^%]+)%(?P<route_domain>[0-9]+)[:.](?P<port>[0-9]+|any)'
        matches = re.search(pattern, destination)
        if matches:
            try:
                port = int(matches.group('port'))
            except ValueError:
                # Can be a port of "any". This only happens with IPv6
                port = matches.group('port')
                if port == 'any':
                    port = 0
            ip = matches.group('ip')
            if not self.is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=matches.group('ip'),
                port=port,
                route_domain=int(matches.group('route_domain'))
            )
            return result

        pattern = r'(?P<ip>[^%]+)%(?P<route_domain>[0-9]+)'
        matches = re.search(pattern, destination)
        if matches:
            ip = matches.group('ip')
            if not self.is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=matches.group('ip'),
                port=None,
                route_domain=int(matches.group('route_domain'))
            )
            return result

        parts = destination.split('.')
        if len(parts) == 4:
            # IPv4
            ip, port = destination.split(':')
            if not self.is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=ip,
                port=int(port),
                route_domain=None
            )
            return result
        elif len(parts) == 2:
            # IPv6
            ip, port = destination.split('.')
            try:
                port = int(port)
            except ValueError:
                # Can be a port of "any". This only happens with IPv6
                if port == 'any':
                    port = 0
            if not self.is_valid_ip(ip):
                raise F5ModuleError(
                    "The provided destination is not a valid IP address"
                )
            result = Destination(
                ip=ip,
                port=port,
                route_domain=None
            )
            return result
        else:
            result = Destination(ip=None, port=None, route_domain=None)
            return result

    @property
    def port(self):
        destination = self.destination_tuple
        self._values['port'] = destination.port
        return destination.port

    @property
    def route_domain(self):
        """Return a route domain number from the destination

        Returns:
            int: The route domain number
        """
        destination = self.destination_tuple
        self._values['route_domain'] = destination.route_domain
        return int(destination.route_domain)

    @property
    def profiles(self):
        """Returns a list of profiles from the API

        The profiles are formatted so that they are usable in this module and
        are able to be compared by the Difference engine.

        Returns:
             list (:obj:`list` of :obj:`dict`): List of profiles.

             Each dictionary in the list contains the following three (3) keys.

             * name
             * context
             * fullPath

        Raises:
            F5ModuleError: If the specified context is a value other that
                ``all``, ``serverside``, or ``clientside``.
        """
        if 'items' not in self._values['profiles']:
            return None
        result = []
        for item in self._values['profiles']['items']:
            context = item['context']
            name = item['name']
            if context in ['all', 'serverside', 'clientside']:
                result.append(dict(name=name, context=context, fullPath=item['fullPath']))
            else:
                raise F5ModuleError(
                    "Unknown profile context found: '{0}'".format(context)
                )
        return result

    @property
    def profile_types(self):
        return [x['name'] for x in iteritems(self.profiles)]

    @property
    def policies(self):
        if 'items' not in self._values['policies']:
            return None
        result = []
        for item in self._values['policies']['items']:
            name = item['name']
            partition = item['partition']
            result.append(dict(name=name, partition=partition))
        return result

    @property
    def default_persistence_profile(self):
        """Get the name of the current default persistence profile

        These persistence profiles are always lists when we get them
        from the REST API even though there can only be one. We'll
        make it a list again when we get to the Difference engine.

        Returns:
             string: The name of the default persistence profile
        """
        if self._values['default_persistence_profile'] is None:
            return None
        return self._values['default_persistence_profile'][0]

    @property
    def enabled(self):
        if 'enabled' in self._values:
            return True
        else:
            return False

    @property
    def disabled(self):
        if 'disabled' in self._values:
            return True
        return False

    @property
    def metadata(self):
        if self._values['metadata'] is None:
            return None
        result = []
        for md in self._values['metadata']:
            tmp = dict(name=str(md['name']))
            if 'value' in md:
                tmp['value'] = str(md['value'])
            else:
                tmp['value'] = ''
            result.append(tmp)
        return result

    @property
    def security_log_profiles(self):
        if self._values['security_log_profiles'] is None:
            return None
        # At the moment, BIG-IP wraps the names of log profiles in double-quotes if
        # the profile name contains spaces. This is likely due to the REST code being
        # too close to actual tmsh code and, at the tmsh level, a space in the profile
        # name would cause tmsh to see the 2nd word (and beyond) as "the next parameter".
        #
        # This seems like a bug to me.
        result = list(set([x.strip('"') for x in self._values['security_log_profiles']]))
        result.sort()
        return result


class ModuleParameters(Parameters):
    services_map = {
        'ftp': 21,
        'http': 80,
        'https': 443,
        'telnet': 23,
        'pptp': 1723,
        'smtp': 25,
        'snmp': 161,
        'snmp-trap': 162,
        'ssh': 22,
        'tftp': 69,
        'isakmp': 500,
        'mqtt': 1883,
        'mqtt-tls': 8883,
        'rtsp': 554
    }

    def _handle_profile_context(self, tmp):
        if 'context' not in tmp:
            tmp['context'] = 'all'
        else:
            if 'name' not in tmp:
                raise F5ModuleError(
                    "A profile name must be specified when a context is specified."
                )
        tmp['context'] = tmp['context'].replace('server-side', 'serverside')
        tmp['context'] = tmp['context'].replace('client-side', 'clientside')

    def _handle_clientssl_profile_nuances(self, profile):
        if profile['name'] != 'clientssl':
            return
        if profile['context'] != 'clientside':
            profile['context'] = 'clientside'

    def _check_port(self):
        try:
            port = int(self._values['port'])
        except ValueError:
            raise F5ModuleError(
                "The specified port was not a valid integer"
            )
        if 0 <= port <= 65535:
            return port
        raise F5ModuleError(
            "Valid ports must be in range 0 - 65535"
        )

    @property
    def destination(self):
        addr = self._values['destination'].split("%")[0]
        if not self.is_valid_ip(addr):
            raise F5ModuleError(
                "The provided destination is not a valid IP address"
            )
        result = self._format_destination(addr, self.port, self.route_domain)
        return result

    @property
    def destination_tuple(self):
        Destination = namedtuple('Destination', ['ip', 'port', 'route_domain'])
        if self._values['destination'] is None:
            result = Destination(ip=None, port=None, route_domain=None)
            return result
        addr = self._values['destination'].split("%")[0]
        result = Destination(ip=addr, port=self.port, route_domain=self.route_domain)
        return result

    @property
    def source(self):
        if self._values['source'] is None:
            return None
        try:
            addr = netaddr.IPNetwork(self._values['source'])
            result = '{0}/{1}'.format(str(addr.ip), addr.prefixlen)
            return result
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The source IP address must be specified in CIDR format: address/prefix"
            )

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        if self._values['port'] in ['*', 'any']:
            return 0
        if self._values['port'] in self.services_map:
            port = self._values['port']
            self._values['port'] = self.services_map[port]
        self._check_port()
        return int(self._values['port'])

    @property
    def irules(self):
        results = []
        if self._values['irules'] is None:
            return None
        if len(self._values['irules']) == 1 and self._values['irules'][0] == '':
            return ''
        for irule in self._values['irules']:
            result = fq_name(self.partition, irule)
            results.append(result)
        return results

    @property
    def profiles(self):
        if self._values['profiles'] is None:
            return None
        if len(self._values['profiles']) == 1 and self._values['profiles'][0] == '':
            return ''
        result = []
        for profile in self._values['profiles']:
            tmp = dict()
            if isinstance(profile, dict):
                tmp.update(profile)
                self._handle_profile_context(tmp)
                if 'name' not in profile:
                    tmp['name'] = profile
                tmp['fullPath'] = fq_name(self.partition, tmp['name'])
                self._handle_clientssl_profile_nuances(tmp)
            else:
                tmp['name'] = profile
                tmp['context'] = 'all'
                tmp['fullPath'] = fq_name(self.partition, tmp['name'])
                self._handle_clientssl_profile_nuances(tmp)
            result.append(tmp)
        mutually_exclusive = [x['name'] for x in result if x in self.profiles_mutex]
        if len(mutually_exclusive) > 1:
            raise F5ModuleError(
                "Profiles {0} are mutually exclusive".format(
                    ', '.join(self.profiles_mutex).strip()
                )
            )
        return result

    @property
    def policies(self):
        if self._values['policies'] is None:
            return None
        if len(self._values['policies']) == 1 and self._values['policies'][0] == '':
            return ''
        result = []
        policies = [fq_name(self.partition, p) for p in self._values['policies']]
        policies = set(policies)
        for policy in policies:
            parts = policy.split('/')
            if len(parts) != 3:
                raise F5ModuleError(
                    "The specified policy '{0}' is malformed".format(policy)
                )
            tmp = dict(
                name=parts[2],
                partition=parts[1]
            )
            result.append(tmp)
        return result

    @property
    def pool(self):
        if self._values['pool'] is None:
            return None
        if self._values['pool'] == '':
            return ''
        return fq_name(self.partition, self._values['pool'])

    @property
    def vlans_enabled(self):
        if self._values['enabled_vlans'] is None:
            return None
        elif self._values['vlans_enabled'] is False:
            # This is a special case for "all" enabled VLANs
            return False
        if self._values['disabled_vlans'] is None:
            return True
        return False

    @property
    def vlans_disabled(self):
        if self._values['disabled_vlans'] is None:
            return None
        elif self._values['vlans_disabled'] is True:
            # This is a special case for "all" enabled VLANs
            return True
        elif self._values['enabled_vlans'] is None:
            return True
        return False

    @property
    def enabled_vlans(self):
        if self._values['enabled_vlans'] is None:
            return None
        elif any(x.lower() for x in self._values['enabled_vlans'] if x.lower() in ['all', '*']):
            result = [fq_name(self.partition, 'all')]
            if result[0].endswith('/all'):
                if self._values['__warnings'] is None:
                    self._values['__warnings'] = []
                self._values['__warnings'].append(
                    dict(
                        msg="Usage of the 'ALL' value for 'enabled_vlans' parameter is deprecated. Use '*' instead",
                        version='2.5'
                    )
                )
            return result
        results = list(set([fq_name(self.partition, x) for x in self._values['enabled_vlans']]))
        results.sort()
        return results

    @property
    def disabled_vlans(self):
        if self._values['disabled_vlans'] is None:
            return None
        elif any(x.lower() for x in self._values['disabled_vlans'] if x.lower() in ['all', '*']):
            raise F5ModuleError(
                "You cannot disable all VLANs. You must name them individually."
            )
        results = list(set([fq_name(self.partition, x) for x in self._values['disabled_vlans']]))
        results.sort()
        return results

    @property
    def vlans(self):
        disabled = self.disabled_vlans
        if disabled:
            return self.disabled_vlans
        return self.enabled_vlans

    @property
    def state(self):
        if self._values['state'] == 'present':
            return 'enabled'
        return self._values['state']

    @property
    def snat(self):
        if self._values['snat'] is None:
            return None
        lowercase = self._values['snat'].lower()
        if lowercase in ['automap', 'none']:
            return dict(type=lowercase)
        snat_pool = fq_name(self.partition, self._values['snat'])
        return dict(pool=snat_pool, type='snat')

    @property
    def default_persistence_profile(self):
        if self._values['default_persistence_profile'] is None:
            return None
        if self._values['default_persistence_profile'] == '':
            return ''
        profile = fq_name(self.partition, self._values['default_persistence_profile'])
        parts = profile.split('/')
        if len(parts) != 3:
            raise F5ModuleError(
                "The specified 'default_persistence_profile' is malformed"
            )
        result = dict(
            name=parts[2],
            partition=parts[1]
        )
        return result

    @property
    def fallback_persistence_profile(self):
        if self._values['fallback_persistence_profile'] is None:
            return None
        if self._values['fallback_persistence_profile'] == '':
            return ''
        result = fq_name(self.partition, self._values['fallback_persistence_profile'])
        return result

    @property
    def enabled(self):
        if self._values['state'] == 'enabled':
            return True
        elif self._values['state'] == 'disabled':
            return False
        else:
            return None

    @property
    def disabled(self):
        if self._values['state'] == 'enabled':
            return False
        elif self._values['state'] == 'disabled':
            return True
        else:
            return None

    @property
    def metadata(self):
        if self._values['metadata'] is None:
            return None
        if self._values['metadata'] == '':
            return []
        result = []
        try:
            for k, v in iteritems(self._values['metadata']):
                tmp = dict(name=str(k))
                if v:
                    tmp['value'] = str(v)
                else:
                    tmp['value'] = ''
                result.append(tmp)
        except AttributeError:
            raise F5ModuleError(
                "The 'metadata' parameter must be a dictionary of key/value pairs."
            )
        return result

    @property
    def address_translation(self):
        if self._values['address_translation'] is None:
            return None
        if self._values['address_translation']:
            return 'enabled'
        return 'disabled'

    @property
    def port_translation(self):
        if self._values['port_translation'] is None:
            return None
        if self._values['port_translation']:
            return 'enabled'
        return 'disabled'

    @property
    def firewall_enforced_policy(self):
        if self._values['firewall_enforced_policy'] is None:
            return None
        return fq_name(self.partition, self._values['firewall_enforced_policy'])

    @property
    def firewall_staged_policy(self):
        if self._values['firewall_staged_policy'] is None:
            return None
        return fq_name(self.partition, self._values['firewall_staged_policy'])

    @property
    def security_log_profiles(self):
        if self._values['security_log_profiles'] is None:
            return None
        if len(self._values['security_log_profiles']) == 1 and self._values['security_log_profiles'][0] == '':
            return ''
        result = list(set([fq_name(self.partition, x) for x in self._values['security_log_profiles']]))
        result.sort()
        return result


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def destination(self):
        if self._values['type'] == 'internal':
            return None
        return self._values['destination']

    @property
    def vlans(self):
        if self._values['vlans'] is None:
            return None
        elif len(self._values['vlans']) == 0:
            return []
        elif any(x for x in self._values['vlans'] if x.lower() in ['/common/all', 'all']):
            return []
        return self._values['vlans']

    @property
    def irules(self):
        if self._values['irules'] is None:
            return None
        if self._values['type'] in ['dhcp', 'stateless', 'reject', 'internal']:
            return None
        return self._values['irules']

    @property
    def policies(self):
        if self._values['policies'] is None:
            return None
        if self._values['type'] in ['dhcp', 'reject', 'internal']:
            return None
        return self._values['policies']

    @property
    def default_persistence_profile(self):
        if self._values['default_persistence_profile'] is None:
            return None
        if self._values['type'] == 'dhcp':
            return None
        if not self._values['default_persistence_profile']:
            return []
        return [self._values['default_persistence_profile']]

    @property
    def fallback_persistence_profile(self):
        if self._values['fallback_persistence_profile'] is None:
            return None
        if self._values['type'] == 'dhcp':
            return None
        return self._values['fallback_persistence_profile']

    @property
    def snat(self):
        if self._values['snat'] is None:
            return None
        if self._values['type'] in ['dhcp', 'reject', 'internal']:
            return None
        return self._values['snat']

    @property
    def dhcpRelay(self):
        if self._values['type'] == 'dhcp':
            return True

    @property
    def reject(self):
        if self._values['type'] == 'reject':
            return True

    @property
    def stateless(self):
        if self._values['type'] == 'stateless':
            return True

    @property
    def internal(self):
        if self._values['type'] == 'internal':
            return True

    @property
    def ipForward(self):
        if self._values['type'] == 'forwarding-ip':
            return True

    @property
    def l2Forward(self):
        if self._values['type'] == 'forwarding-l2':
            return True

    @property
    def security_log_profiles(self):
        if self._values['security_log_profiles'] is None:
            return None
        mutex = ('Log all requests', 'Log illegal requests')
        if len([x for x in self._values['security_log_profiles'] if x.endswith(mutex)]) >= 2:
            raise F5ModuleError(
                "The 'Log all requests' and 'Log illegal requests' are mutually exclusive."
            )
        return self._values['security_log_profiles']


class ReportableChanges(Changes):
    @property
    def snat(self):
        if self._values['snat'] is None:
            return None
        result = self._values['snat'].get('type', None)
        if result == 'automap':
            return 'Automap'
        elif result == 'none':
            return 'none'
        result = self._values['snat'].get('pool', None)
        return result

    @property
    def destination(self):
        params = ApiParameters(params=dict(destination=self._values['destination']))
        result = params.destination_tuple.ip
        return result

    @property
    def port(self):
        params = ApiParameters(params=dict(destination=self._values['destination']))
        result = params.destination_tuple.port
        return result

    @property
    def default_persistence_profile(self):
        if len(self._values['default_persistence_profile']) == 0:
            return []
        profile = self._values['default_persistence_profile'][0]
        result = '/{0}/{1}'.format(profile['partition'], profile['name'])
        return result

    @property
    def policies(self):
        if len(self._values['policies']) == 0:
            return []
        result = ['/{0}/{1}'.format(x['partition'], x['name']) for x in self._values['policies']]
        return result

    @property
    def enabled_vlans(self):
        if len(self._values['vlans']) == 0 and self._values['vlans_disabled'] is True:
            return 'all'
        elif len(self._values['vlans']) > 0 and self._values['vlans_enabled'] is True:
            return self._values['vlans']

    @property
    def disabled_vlans(self):
        if len(self._values['vlans']) > 0 and self._values['vlans_disabled'] is True:
            return self._values['vlans']

    @property
    def address_translation(self):
        if self._values['address_translation'] == 'enabled':
            return True
        return False

    @property
    def port_translation(self):
        if self._values['port_translation'] == 'enabled':
            return True
        return False


class VirtualServerValidator(object):
    def __init__(self, module=None, client=None, want=None, have=None):
        self.have = have if have else ApiParameters()
        self.want = want if want else ModuleParameters()
        self.client = client
        self.module = module

    def check_update(self):
        # TODO(Remove in Ansible 2.9)
        self._override_standard_type_from_profiles()

        # Regular checks
        self._override_port_by_type()
        self._override_protocol_by_type()
        self._verify_type_has_correct_profiles()
        self._verify_default_persistence_profile_for_type()
        self._verify_fallback_persistence_profile_for_type()
        self._update_persistence_profile()
        self._ensure_server_type_supports_vlans()
        self._verify_type_has_correct_ip_protocol()

        # For different server types
        self._verify_dhcp_profile()
        self._verify_fastl4_profile()
        self._verify_stateless_profile()

    def check_create(self):
        # TODO(Remove in Ansible 2.9)
        self._override_standard_type_from_profiles()

        # Regular checks
        self._set_default_ip_protocol()
        self._set_default_profiles()
        self._override_port_by_type()
        self._override_protocol_by_type()
        self._verify_type_has_correct_profiles()
        self._verify_default_persistence_profile_for_type()
        self._verify_fallback_persistence_profile_for_type()
        self._update_persistence_profile()
        self._verify_virtual_has_required_parameters()
        self._ensure_server_type_supports_vlans()
        self._override_vlans_if_all_specified()
        self._check_source_and_destination_match()
        self._verify_type_has_correct_ip_protocol()
        self._verify_minimum_profile()

        # For different server types
        self._verify_dhcp_profile()
        self._verify_fastl4_profile()
        self._verify_stateless_profile_on_create()

    def _ensure_server_type_supports_vlans(self):
        """Verifies the specified server type supports VLANs

        A select number of server types do not support VLANs. This method
        checks to see if the specified types were provided along with VLANs.
        If they were, the module will raise an error informing the user that
        they need to either remove the VLANs, or, change the ``type``.

        Returns:
            None: Returned if no VLANs are specified.
        Raises:
            F5ModuleError: Raised if the server type conflicts with VLANs.
        """
        if self.want.enabled_vlans is None:
            return
        if self.want.type == 'internal':
            raise F5ModuleError(
                "The 'internal' server type does not support VLANs."
            )

    def _override_vlans_if_all_specified(self):
        """Overrides any specified VLANs if "all" VLANs are specified

        The special setting "all VLANs" in a BIG-IP requires that no other VLANs
        be specified. If you specify any number of VLANs, AND include the "all"
        VLAN, this method will erase all of the other VLANs and only return the
        "all" VLAN.
        """
        all_vlans = ['/common/all', 'all']
        if self.want.enabled_vlans is not None:
            if any(x for x in self.want.enabled_vlans if x.lower() in all_vlans):
                self.want.update(
                    dict(
                        enabled_vlans=[],
                        vlans_disabled=True,
                        vlans_enabled=False
                    )
                )

    def _override_port_by_type(self):
        if self.want.type == 'dhcp':
            self.want.update({'port': 67})
        elif self.want.type == 'internal':
            self.want.update({'port': 0})

    def _override_protocol_by_type(self):
        if self.want.type in ['stateless']:
            self.want.update({'ip_protocol': 17})

    def _override_standard_type_from_profiles(self):
        """Overrides a standard virtual server type given the specified profiles

        For legacy purposes, this module will do some basic overriding of the default
        ``type`` parameter to support cases where changing the ``type`` only requires
        specifying a different set of profiles.

        Ideally, ``type`` would always be specified, but in the past, this module only
        supported an implicit "standard" type. Module users would specify some different
        types of profiles and this would change the type...in some circumstances.

        Now that this module supports a ``type`` param, the implicit ``type`` changing
        that used to happen is technically deprecated (and will be warned on). Users
        should always specify a ``type`` now, or, accept the default standard type.

        Returns:
            void
        """
        if self.want.type == 'standard':
            if self.want.has_fastl4_profiles:
                self.want.update({'type': 'performance-l4'})
                self.module.deprecate(
                    msg="Specifying 'performance-l4' profiles on a 'standard' type is deprecated and will be removed.",
                    version='2.6'
                )
            if self.want.has_fasthttp_profiles:
                self.want.update({'type': 'performance-http'})
                self.module.deprecate(
                    msg="Specifying 'performance-http' profiles on a 'standard' type is deprecated and will be removed.",
                    version='2.6'
                )
            if self.want.has_message_routing_profiles:
                self.want.update({'type': 'message-routing'})
                self.module.deprecate(
                    msg="Specifying 'message-routing' profiles on a 'standard' type is deprecated and will be removed.",
                    version='2.6'
                )

    def _check_source_and_destination_match(self):
        """Verify that destination and source are of the same IP version

        BIG-IP does not allow for mixing of the IP versions for destination and
        source addresses. For example, a destination IPv6 address cannot be
        associated with a source IPv4 address.

        This method checks that you specified the same IP version for these
        parameters

        Raises:
            F5ModuleError: Raised when the IP versions of source and destination differ.
        """
        if self.want.source and self.want.destination:
            want = netaddr.IPNetwork(self.want.source)
            have = netaddr.IPNetwork(self.want.destination_tuple.ip)
            if want.version != have.version:
                raise F5ModuleError(
                    "The source and destination addresses for the virtual server must be be the same type (IPv4 or IPv6)."
                )

    def _verify_type_has_correct_ip_protocol(self):
        if self.want.ip_protocol is None:
            return
        if self.want.type == 'standard':
            # Standard supports
            # - tcp
            # - udp
            # - sctp
            # - ipsec-ah
            # - ipsec esp
            # - all protocols
            if self.want.ip_protocol not in [6, 17, 132, 51, 50, 'any']:
                raise F5ModuleError(
                    "The 'standard' server type does not support the specified 'ip_protocol'."
                )
        elif self.want.type == 'performance-http':
            # Perf HTTP supports
            #
            # - tcp
            if self.want.ip_protocol not in [6]:
                raise F5ModuleError(
                    "The 'performance-http' server type does not support the specified 'ip_protocol'."
                )
        elif self.want.type == 'stateless':
            # Stateless supports
            #
            # - udp
            if self.want.ip_protocol not in [17]:
                raise F5ModuleError(
                    "The 'stateless' server type does not support the specified 'ip_protocol'."
                )
        elif self.want.type == 'dhcp':
            # DHCP supports no IP protocols
            if self.want.ip_protocol is not None:
                raise F5ModuleError(
                    "The 'dhcp' server type does not support an 'ip_protocol'."
                )
        elif self.want.type == 'internal':
            # Internal supports
            #
            # - tcp
            # - udp
            if self.want.ip_protocol not in [6, 17]:
                raise F5ModuleError(
                    "The 'internal' server type does not support the specified 'ip_protocol'."
                )
        elif self.want.type == 'message-routing':
            # Message Routing supports
            #
            # - tcp
            # - udp
            # - sctp
            # - all protocols
            if self.want.ip_protocol not in [6, 17, 132, 'all']:
                raise F5ModuleError(
                    "The 'message-routing' server type does not support the specified 'ip_protocol'."
                )

    def _verify_virtual_has_required_parameters(self):
        """Verify that the virtual has required parameters

        Virtual servers require several parameters that are not necessarily required
        when updating the virtual. This method will check for the required params
        upon creation.

        Ansible supports ``default`` variables in an Argument Spec, but those defaults
        apply to all operations; including create, update, and delete. Since users are not
        required to always specify these parameters, we cannot use Ansible's facility.
        If we did, and then users would be required to provide them when, for example,
        they attempted to delete a virtual (even though they are not required to delete
        a virtual.

        Raises:
             F5ModuleError: Raised when the user did not specify required parameters.
        """
        required_resources = ['destination', 'port']
        if self.want.type == 'internal':
            return
        if all(getattr(self.want, v) is None for v in required_resources):
            raise F5ModuleError(
                "You must specify both of " + ', '.join(required_resources)
            )

    def _verify_default_persistence_profile_for_type(self):
        """Verify that the server type supports default persistence profiles

        Verifies that the specified server type supports default persistence profiles.
        Some virtual servers do not support these types of profiles. This method will
        check that the type actually supports what you are sending it.

        Types that do not, at this time, support default persistence profiles include,

        * dhcp
        * message-routing
        * reject
        * stateless
        * forwarding-ip
        * forwarding-l2

        Raises:
            F5ModuleError: Raised if server type does not support default persistence profiles.
        """
        default_profile_not_allowed = [
            'dhcp', 'message-routing', 'reject', 'stateless', 'forwarding-ip', 'forwarding-l2'
        ]
        if self.want.ip_protocol in default_profile_not_allowed:
            raise F5ModuleError(
                "The '{0}' server type does not support a 'default_persistence_profile'".format(self.want.type)
            )

    def _verify_fallback_persistence_profile_for_type(self):
        """Verify that the server type supports fallback persistence profiles

        Verifies that the specified server type supports fallback persistence profiles.
        Some virtual servers do not support these types of profiles. This method will
        check that the type actually supports what you are sending it.

        Types that do not, at this time, support fallback persistence profiles include,

        * dhcp
        * message-routing
        * reject
        * stateless
        * forwarding-ip
        * forwarding-l2
        * performance-http

        Raises:
            F5ModuleError: Raised if server type does not support fallback persistence profiles.
        """
        default_profile_not_allowed = [
            'dhcp', 'message-routing', 'reject', 'stateless', 'forwarding-ip', 'forwarding-l2',
            'performance-http'
        ]
        if self.want.ip_protocol in default_profile_not_allowed:
            raise F5ModuleError(
                "The '{0}' server type does not support a 'fallback_persistence_profile'".format(self.want.type)
            )

    def _update_persistence_profile(self):
        # This must be changed back to a list to make a valid REST API
        # value. The module manipulates this as a normal dictionary
        if self.want.default_persistence_profile is not None:
            self.want.update({'default_persistence_profile': self.want.default_persistence_profile})

    def _verify_type_has_correct_profiles(self):
        """Verify that specified server type does not include forbidden profiles

        The type of the server determines the ``type``s of profiles that it accepts. This
        method checks that the server ``type`` that you specified is indeed one that can
        accept the profiles that you specified.

        The common situations are

        * ``standard`` types that include ``fasthttp``, ``fastl4``, or ``message routing`` profiles
        * ``fasthttp`` types that are missing a ``fasthttp`` profile
        * ``fastl4`` types that are missing a ``fastl4`` profile
        * ``message-routing`` types that are missing ``diameter`` or ``sip`` profiles

        Raises:
            F5ModuleError: Raised when a validation check fails.
        """
        if self.want.type == 'standard':
            if self.want.has_fasthttp_profiles:
                raise F5ModuleError("A 'standard' type may not have 'fasthttp' profiles.")
            if self.want.has_fastl4_profiles:
                raise F5ModuleError("A 'standard' type may not have 'fastl4' profiles.")
            if self.want.has_message_routing_profiles:
                raise F5ModuleError("A 'standard' type may not have 'message-routing' profiles.")
        elif self.want.type == 'performance-http':
            if not self.want.has_fasthttp_profiles:
                raise F5ModuleError("A 'fasthttp' type must have at least one 'fasthttp' profile.")
        elif self.want.type == 'performance-l4':
            if not self.want.has_fastl4_profiles:
                raise F5ModuleError("A 'fastl4' type must have at least one 'fastl4' profile.")
        elif self.want.type == 'message-routing':
            if not self.want.has_message_routing_profiles:
                raise F5ModuleError("A 'message-routing' type must have either a 'sip' or 'diameter' profile.")

    def _set_default_ip_protocol(self):
        if self.want.type == 'dhcp':
            return
        if self.want.ip_protocol is None:
            self.want.update({'ip_protocol': 6})

    def _set_default_profiles(self):
        if self.want.type == 'standard':
            if not self.want.profiles:
                # Sets a default profiles when creating a new standard virtual.
                #
                # It appears that if no profiles are deliberately specified, then under
                # certain circumstances, the server type will default to ``performance-l4``.
                #
                # It's unclear what these circumstances are, but they are met in issue 00093.
                # If this block of profile setting code is removed, the virtual server's
                # type will change to performance-l4 for some reason.
                #
                if self.want.ip_protocol == 6:
                    self.want.update({'profiles': ['tcp']})
                if self.want.ip_protocol == 17:
                    self.want.update({'profiles': ['udp']})
                if self.want.ip_protocol == 132:
                    self.want.update({'profiles': ['sctp']})

    def _verify_minimum_profile(self):
        if self.want.profiles:
            return None
        if self.want.type == 'internal' and self.want.profiles == '':
            raise F5ModuleError(
                "An 'internal' server must have at least one profile relevant to its 'ip_protocol'. "
                "For example, 'tcp', 'udp', or variations of those."
            )

    def _verify_dhcp_profile(self):
        if self.want.type != 'dhcp':
            return
        if self.want.profiles is None:
            return
        have = set(self.read_dhcp_profiles_from_device())
        want = set([x['fullPath'] for x in self.want.profiles])
        if have.intersection(want):
            return True
        raise F5ModuleError(
            "A dhcp profile, such as 'dhcpv4', or 'dhcpv6' must be specified when 'type' is 'dhcp'."
        )

    def _verify_fastl4_profile(self):
        if self.want.type != 'performance-l4':
            return
        if self.want.profiles is None:
            return
        have = set(self.read_fastl4_profiles_from_device())
        want = set([x['fullPath'] for x in self.want.profiles])
        if have.intersection(want):
            return True
        raise F5ModuleError(
            "A performance-l4 profile, such as 'fastL4', must be specified when 'type' is 'performance-l4'."
        )

    def _verify_fasthttp_profile(self):
        if self.want.type != 'performance-http':
            return
        if self.want.profiles is None:
            return
        have = set(self.read_fasthttp_profiles_from_device())
        want = set([x['fullPath'] for x in self.want.profiles])
        if have.intersection(want):
            return True
        raise F5ModuleError(
            "A performance-http profile, such as 'fasthttp', must be specified when 'type' is 'performance-http'."
        )

    def _verify_stateless_profile_on_create(self):
        if self.want.type != 'stateless':
            return
        result = self._verify_stateless_profile()
        if result is None:
            raise F5ModuleError(
                "A udp profile, must be specified when 'type' is 'stateless'."
            )

    def _verify_stateless_profile(self):
        if self.want.type != 'stateless':
            return
        if self.want.profiles is None:
            return
        have = set(self.read_udp_profiles_from_device())
        want = set([x['fullPath'] for x in self.want.profiles])
        if have.intersection(want):
            return True
        raise F5ModuleError(
            "A udp profile, must be specified when 'type' is 'stateless'."
        )

    def read_dhcp_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.dhcpv4s.get_collection()
        result = [fq_name(self.want.partition, x.name) for x in collection]
        collection = self.client.api.tm.ltm.profile.dhcpv6s.get_collection()
        result += [fq_name(self.want.partition, x.name) for x in collection]
        return result

    def read_fastl4_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.fastl4s.get_collection()
        result = [fq_name(self.want.partition, x.name) for x in collection]
        return result

    def read_fasthttp_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.fasthttps.get_collection()
        result = [fq_name(self.want.partition, x.name) for x in collection]
        return result

    def read_udp_profiles_from_device(self):
        collection = self.client.api.tm.ltm.profile.udps.get_collection()
        result = [fq_name(self.want.partition, x.name) for x in collection]
        return result


class Difference(object):
    def __init__(self, want, have=None):
        self.have = have
        self.want = want

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            result = self.__default(param)
            return result

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    def to_tuple(self, items):
        result = []
        for x in items:
            tmp = [(str(k), str(v)) for k, v in iteritems(x)]
            result += tmp
        return result

    def _diff_complex_items(self, want, have):
        if want == [] and have is None:
            return None
        if want is None:
            return None
        w = self.to_tuple(want)
        h = self.to_tuple(have)
        if set(w).issubset(set(h)):
            return None
        else:
            return want

    def _update_vlan_status(self, result):
        if self.want.vlans_disabled is not None:
            if self.want.vlans_disabled != self.have.vlans_disabled:
                result['vlans_disabled'] = self.want.vlans_disabled
                result['vlans_enabled'] = not self.want.vlans_disabled
        elif self.want.vlans_enabled is not None:
            if any(x.lower().endswith('/all') for x in self.want.vlans):
                if self.have.vlans_enabled is True:
                    result['vlans_disabled'] = True
                    result['vlans_enabled'] = False
            elif self.want.vlans_enabled != self.have.vlans_enabled:
                result['vlans_disabled'] = not self.want.vlans_enabled
                result['vlans_enabled'] = self.want.vlans_enabled

    @property
    def destination(self):
        # The internal type does not support the 'destination' parameter, so it is ignored.
        if self.want.type == 'internal':
            return

        addr_tuple = [self.want.destination, self.want.port, self.want.route_domain]
        if all(x for x in addr_tuple if x is None):
            return None

        have = self.have.destination_tuple

        if self.want.port is None:
            self.want.update({'port': have.port})
        if self.want.route_domain is None:
            self.want.update({'route_domain': have.route_domain})
        if self.want.destination_tuple.ip is None:
            address = have.ip
        else:
            address = self.want.destination_tuple.ip

        want = self.want._format_destination(address, self.want.port, self.want.route_domain)
        if want != self.have.destination:
            return fq_name(self.want.partition, want)

    @property
    def source(self):
        if self.want.source is None:
            return None
        want = netaddr.IPNetwork(self.want.source)
        have = netaddr.IPNetwork(self.have.destination_tuple.ip)
        if want.version != have.version:
            raise F5ModuleError(
                "The source and destination addresses for the virtual server must be be the same type (IPv4 or IPv6)."
            )
        if self.want.source != self.have.source:
            return self.want.source

    @property
    def vlans(self):
        if self.want.vlans is None:
            return None
        elif self.want.vlans == [] and self.have.vlans is None:
            return None
        elif self.want.vlans == self.have.vlans:
            return None

        # Specifically looking for /all because the vlans return value will be
        # an FQDN list. This means that "all" will be returned as "/partition/all",
        # ex, /Common/all.
        #
        # We do not want to accidentally match values that would end with the word
        # "all", like "vlansall". Therefore we look for the forward slash because this
        # is a path delimiter.
        elif any(x.lower().endswith('/all') for x in self.want.vlans):
            if self.have.vlans is None:
                return None
            else:
                return []
        else:
            return self.want.vlans

    @property
    def enabled_vlans(self):
        return self.vlan_status

    @property
    def disabled_vlans(self):
        return self.vlan_status

    @property
    def vlan_status(self):
        result = dict()
        vlans = self.vlans
        if vlans is not None:
            result['vlans'] = vlans
        self._update_vlan_status(result)
        return result

    @property
    def port(self):
        result = self.destination
        if result is not None:
            return dict(
                destination=result
            )

    @property
    def profiles(self):
        if self.want.profiles is None:
            return None
        if self.want.profiles == '' and len(self.have.profiles) > 0:
            have = set([(p['name'], p['context'], p['fullPath']) for p in self.have.profiles])
            if len(self.have.profiles) == 1:
                if not any(x[0] in ['tcp', 'udp', 'sctp'] for x in have):
                    return []
                else:
                    return None
            else:
                return []
        if self.want.profiles == '' and len(self.have.profiles) == 0:
            return None
        want = set([(p['name'], p['context'], p['fullPath']) for p in self.want.profiles])
        have = set([(p['name'], p['context'], p['fullPath']) for p in self.have.profiles])

        if len(have) == 0:
            return self.want.profiles
        elif len(have) == 1:
            if want != have:
                return self.want.profiles
        else:
            if not any(x[0] == 'tcp' for x in want):
                if self.want.type != 'stateless':
                    have = set([x for x in have if x[0] != 'tcp'])
            if not any(x[0] == 'udp' for x in want):
                have = set([x for x in have if x[0] != 'udp'])
            if not any(x[0] == 'sctp' for x in want):
                if self.want.type != 'stateless':
                    have = set([x for x in have if x[0] != 'sctp'])
            want = set([(p[2], p[1]) for p in want])
            have = set([(p[2], p[1]) for p in have])
            if want != have:
                return self.want.profiles

    @property
    def ip_protocol(self):
        if self.want.ip_protocol != self.have.ip_protocol:
            return self.want.ip_protocol

    @property
    def fallback_persistence_profile(self):
        if self.want.fallback_persistence_profile is None:
            return None
        if self.want.fallback_persistence_profile == '' and self.have.fallback_persistence_profile is not None:
            return ""
        if self.want.fallback_persistence_profile == '' and self.have.fallback_persistence_profile is None:
            return None
        if self.want.fallback_persistence_profile != self.have.fallback_persistence_profile:
            return self.want.fallback_persistence_profile

    @property
    def default_persistence_profile(self):
        if self.want.default_persistence_profile is None:
            return None
        if self.want.default_persistence_profile == '' and self.have.default_persistence_profile is not None:
            return []
        if self.want.default_persistence_profile == '' and self.have.default_persistence_profile is None:
            return None
        if self.have.default_persistence_profile is None:
            return dict(
                default_persistence_profile=self.want.default_persistence_profile
            )
        w_name = self.want.default_persistence_profile.get('name', None)
        w_partition = self.want.default_persistence_profile.get('partition', None)
        h_name = self.have.default_persistence_profile.get('name', None)
        h_partition = self.have.default_persistence_profile.get('partition', None)
        if w_name != h_name or w_partition != h_partition:
            return dict(
                default_persistence_profile=self.want.default_persistence_profile
            )

    @property
    def policies(self):
        if self.want.policies is None:
            return None
        if self.want.policies == '' and self.have.policies is None:
            return None
        if self.want.policies == '' and len(self.have.policies) > 0:
            return []
        if not self.have.policies:
            return self.want.policies
        want = set([(p['name'], p['partition']) for p in self.want.policies])
        have = set([(p['name'], p['partition']) for p in self.have.policies])
        if not want == have:
            return self.want.policies

    @property
    def snat(self):
        if self.want.snat is None:
            return None
        if self.want.snat['type'] != self.have.snat['type']:
            result = dict(snat=self.want.snat)
            return result

        if self.want.snat.get('pool', None) is None:
            return None

        if self.want.snat['pool'] != self.have.snat['pool']:
            result = dict(snat=self.want.snat)
            return result

    @property
    def enabled(self):
        if self.want.state == 'enabled' and self.have.disabled:
            result = dict(
                enabled=True,
                disabled=False
            )
            return result
        elif self.want.state == 'disabled' and self.have.enabled:
            result = dict(
                enabled=False,
                disabled=True
            )
            return result

    @property
    def irules(self):
        if self.want.irules is None:
            return None
        if self.want.irules == '' and len(self.have.irules) > 0:
            return []
        if self.want.irules == '' and len(self.have.irules) == 0:
            return None
        if sorted(set(self.want.irules)) != sorted(set(self.have.irules)):
            return self.want.irules

    @property
    def pool(self):
        if self.want.pool is None:
            return None
        if self.want.pool == '' and self.have.pool is not None:
            return ""
        if self.want.pool == '' and self.have.pool is None:
            return None
        if self.want.pool != self.have.pool:
            return self.want.pool

    @property
    def metadata(self):
        if self.want.metadata is None:
            return None
        elif len(self.want.metadata) == 0 and self.have.metadata is None:
            return None
        elif len(self.want.metadata) == 0:
            return []
        elif self.have.metadata is None:
            return self.want.metadata
        result = self._diff_complex_items(self.want.metadata, self.have.metadata)
        return result

    @property
    def type(self):
        if self.want.type != self.have.type:
            raise F5ModuleError(
                "Changing the 'type' parameter is not supported."
            )

    @property
    def security_log_profiles(self):
        if self.want.security_log_profiles is None:
            return None
        if self.have.security_log_profiles is None and self.want.security_log_profiles == '':
            return None
        if self.have.security_log_profiles is not None and self.want.security_log_profiles == '':
            return []
        if self.have.security_log_profiles is None:
            return self.want.security_log_profiles
        if set(self.want.security_log_profiles) != set(self.have.security_log_profiles):
            return self.want.security_log_profiles


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = ApiParameters(client=self.client)
        self.want = ModuleParameters(client=self.client, params=self.module.params)
        self.changes = UsableChanges()

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['present', 'enabled', 'disabled']:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def update(self):
        self.have = self.read_current_from_device()
        validator = VirtualServerValidator(module=self.module, client=self.client, have=self.have, want=self.want)
        validator.check_update()

        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource")
        return True

    def get_reportable_changes(self):
        result = ReportableChanges(params=self.changes.to_return())
        return result

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

    def exists(self):
        result = self.client.api.tm.ltm.virtuals.virtual.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def create(self):
        validator = VirtualServerValidator(module=self.module, client=self.client, have=self.have, want=self.want)
        validator.check_create()

        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.ltm.virtuals.virtual.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def read_current_from_device(self):
        result = self.client.api.tm.ltm.virtuals.virtual.load(
            name=self.want.name,
            partition=self.want.partition,
            requests_params=dict(
                params=dict(
                    expandSubcollections='true'
                )
            )
        )
        params = result.attrs
        params.update(dict(kind=result.to_dict().get('kind', None)))
        result = ApiParameters(params=params, client=self.client)
        return result

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.ltm.virtuals.virtual.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        resource = self.client.api.tm.ltm.virtuals.virtual.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            state=dict(
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
            ),
            name=dict(
                required=True,
                aliases=['vs']
            ),
            destination=dict(
                aliases=['address', 'ip']
            ),
            port=dict(),
            profiles=dict(
                type='list',
                aliases=['all_profiles'],
                options=dict(
                    name=dict(),
                    context=dict(default='all', choices=['all', 'server-side', 'client-side'])
                )
            ),
            policies=dict(
                type='list',
                aliases=['all_policies']
            ),
            irules=dict(
                type='list',
                aliases=['all_rules']
            ),
            enabled_vlans=dict(
                type='list'
            ),
            disabled_vlans=dict(
                type='list'
            ),
            pool=dict(),
            description=dict(),
            snat=dict(),
            default_persistence_profile=dict(),
            fallback_persistence_profile=dict(),
            source=dict(),
            metadata=dict(type='raw'),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            address_translation=dict(type='bool'),
            port_translation=dict(type='bool'),
            ip_protocol=dict(
                choices=[
                    'ah', 'bna', 'esp', 'etherip', 'gre', 'icmp', 'ipencap', 'ipv6',
                    'ipv6-auth', 'ipv6-crypt', 'ipv6-icmp', 'isp-ip', 'mux', 'ospf',
                    'sctp', 'tcp', 'udp', 'udplite'
                ]
            ),
            type=dict(
                default='standard',
                choices=[
                    'standard', 'forwarding-ip', 'forwarding-l2', 'internal', 'message-routing',
                    'performance-http', 'performance-l4', 'reject', 'stateless', 'dhcp'
                ]
            ),
            firewall_staged_policy=dict(),
            firewall_enforced_policy=dict(),
            security_log_profiles=dict(type='list')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['enabled_vlans', 'disabled_vlans']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")
    if not HAS_NETADDR:
        module.fail_json(msg="The python netaddr module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        module.exit_json(**results)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
