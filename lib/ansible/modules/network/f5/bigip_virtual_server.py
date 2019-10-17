#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

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
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
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
    type: str
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
    type: str
    required: True
    aliases:
      - vs
  destination:
    description:
      - Destination IP of the virtual server.
      - Required when C(state) is C(present) and virtual server does not exist.
      - When C(type) is C(internal), this parameter is ignored. For all other types,
        it is required.
      - Destination can also be specified as a name for an existing Virtual Address.
    type: str
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
    type: str
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
    type: str
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
      - B(Profiles matter). This module will fail to configure a BIG-IP if you mix up
        your profiles, or, if you attempt to set an IP protocol which your current,
        or new, profiles do not support. Both this module, and BIG-IP, will tell you
        when you are wrong, with an error resembling C(lists profiles incompatible
        with its protocol).
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
        type: str
      context:
        description:
          - The side of the connection on which the profile should be applied.
        type: str
        choices:
          - all
          - server-side
          - client-side
        default: all
    type: list
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
    type: list
    aliases:
      - all_rules
  enabled_vlans:
    description:
      - List of VLANs to be enabled. When a VLAN named C(all) is used, all
        VLANs will be allowed. VLANs can be specified with or without the
        leading partition. If the partition is not specified in the VLAN,
        then the C(partition) option of this module will be used.
      - This parameter is mutually exclusive with the C(disabled_vlans) parameter.
    type: list
    version_added: 2.2
  disabled_vlans:
    description:
      - List of VLANs to be disabled. If the partition is not specified in the VLAN,
        then the C(partition) option of this module will be used.
      - This parameter is mutually exclusive with the C(enabled_vlans) parameters.
    type: list
    version_added: 2.5
  pool:
    description:
      - Default pool for the virtual server.
      - If you want to remove the existing pool, specify an empty value; C("").
        See the documentation for an example.
      - When creating a new virtual server, and C(type) is C(stateless), this parameter
        is required.
      - If C(type) is C(stateless), the C(pool) that is used must not have any members
        which define a C(rate_limit).
    type: str
  policies:
    description:
      - Specifies the policies for the virtual server.
      - When C(type) is C(dhcp), this parameter will be ignored.
      - When C(type) is C(reject), this parameter will be ignored.
      - When C(type) is C(internal), this parameter will be ignored.
    type: list
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
    type: str
  default_persistence_profile:
    description:
      - Default Profile which manages the session persistence.
      - If you want to remove the existing default persistence profile, specify an
        empty value; C(""). See the documentation for an example.
      - When C(type) is C(dhcp), this parameter will be ignored.
    type: str
  description:
    description:
      - Virtual server description.
    type: str
  fallback_persistence_profile:
    description:
      - Specifies the persistence profile you want the system to use if it
        cannot use the specified default persistence profile.
      - If you want to remove the existing fallback persistence profile, specify an
        empty value; C(""). See the documentation for an example.
      - When C(type) is C(dhcp), this parameter will be ignored.
    type: str
    version_added: 2.3
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
  metadata:
    description:
      - Arbitrary key/value pairs that you can attach to a virtual server. This is useful in
        situations where you might want to annotate a virtual to be managed by Ansible.
      - Key names will be stored as strings; this includes names that are numbers.
      - Values for all of the keys will be stored as strings; this includes values
        that are numbers.
      - Data will be persisted, not ephemeral.
    type: raw
    version_added: 2.5
  insert_metadata:
    description:
      - When set to C(no) it will not set metadata on the device.
      - Currently there is a limitation that non-admin users cannot set metadata on the object, despite being
        able to create and modify virtual server objects, setting this option to C(no) will allow
        such users to utilize this module to manage Virtual Server objects on the device.
    type: bool
    default: yes
    version_added: 2.8
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
  source_port:
    description:
      - Specifies whether the system preserves the source port of the connection.
      - When creating a new virtual server, if this parameter is not specified, the default is C(preserve).
    type: str
    choices:
      - preserve
      - preserve-strict
      - change
    version_added: 2.8
  mirror:
    description:
      - Specifies that the system mirrors connections on each member of a redundant pair.
      - When creating a new virtual server, if this parameter is not specified, the default is C(disabled).
    type: bool
    version_added: 2.8
  mask:
   description:
      - Specifies the destination address network mask. This parameter will work with IPv4 and IPv6 type of addresses.
      - This is an optional parameter which can be specified when creating or updating virtual server.
      - If C(destination) is set in CIDR notation format and C(mask) is provided the C(mask) parameter takes precedence.
      - If catchall destination is specified, i.e. C(0.0.0.0) for IPv4 C(::) for IPv6,
        mask parameter is set to C(any) or C(any6) respectively.
      - When the C(destination) is provided not in CIDR notation and C(mask) is not specified, C(255.255.255.255) or
        C(ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff) is set for IPv4 and IPv6 addresses respectively.
      - When C(destination) is provided in CIDR notation format and C(mask) is not specified the mask parameter is
        inferred from C(destination).
      - When C(destination) is provided as Virtual Address name, and C(mask) is not specified,
        the mask will be C(None) allowing device set it with its internal defaults.
   type: str
   version_added: 2.8
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
    type: str
    choices:
      - ah
      - any
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
    type: str
    version_added: 2.6
  firewall_staged_policy:
    description:
      - Applies the specify AFM policy to the virtual in an enforcing way.
      - A staged policy shows the results of the policy rules in the log, while not
        actually applying the rules to traffic.
      - When creating a new virtual, if this parameter is not specified, the staged
        policy is disabled.
    type: str
    version_added: 2.6
  security_log_profiles:
    description:
      - Specifies the log profile applied to the virtual server.
      - To make use of this feature, the AFM module must be licensed and provisioned.
      - The C(Log all requests) and C(Log illegal requests) are mutually exclusive and
        therefore, this module will raise an error if the two are specified together.
    type: list
    version_added: 2.6
  security_nat_policy:
    description:
      - Specify the Firewall NAT policies for the virtual server.
      - You can specify one or more NAT policies to use.
      - The most specific policy is used. For example, if you specify that the
        virtual server use the device policy and the route domain policy, the route
        domain policy overrides the device policy.
    version_added: 2.7
    suboptions:
      policy:
        description:
          - Policy to apply a NAT policy directly to the virtual server.
          - The virtual server NAT policy is the most specific, and overrides a
            route domain and device policy, if specified.
          - To remove the policy, specify an empty string value.
        type: str
      use_device_policy:
        description:
          - Specify that the virtual server uses the device NAT policy, as specified
            in the Firewall Options.
          - The device policy is used if no route domain or virtual server NAT
            setting is specified.
        type: bool
      use_route_domain_policy:
        description:
          - Specify that the virtual server uses the route domain policy, as
            specified in the Route Domain Security settings.
          - When specified, the route domain policy overrides the device policy, and
            is overridden by a virtual server policy.
        type: bool
    type: dict
  ip_intelligence_policy:
    description:
      - Specifies the IP intelligence policy applied to the virtual server.
      - This parameter requires that a valid BIG-IP security module such as ASM or AFM
        be provisioned.
    type: str
    version_added: 2.8
  rate_limit:
    description:
      - Virtual server rate limit (connections-per-second). Setting this to 0
        disables the limit.
      - The valid value range is C(0) - C(4294967295).
    type: int
    version_added: 2.8
  rate_limit_dst_mask:
    description:
      - Specifies a mask, in bits, to be applied to the destination address as part of the rate limiting.
      - The default value is C(0), which is equivalent to using the entire address - C(32) in IPv4, or C(128) in IPv6.
      - The valid value range is C(0) - C(4294967295).
    type: int
    version_added: 2.8
  rate_limit_src_mask:
    description:
      - Specifies a mask, in bits, to be applied to the source address as part of the rate limiting.
      - The default value is C(0), which is equivalent to using the entire address - C(32) in IPv4, or C(128) in IPv6.
      - The valid value range is C(0) - C(4294967295).
    type: int
    version_added: 2.8
  rate_limit_mode:
    description:
      - Indicates whether the rate limit is applied per virtual object, per source address, per destination address,
        or some combination thereof.
      - The default value is 'object', which does not use the source or destination address as part of the key.
    type: str
    choices:
      - object
      - object-source
      - object-destination
      - object-source-destination
      - destination
      - source
      - source-destination
    default: object
    version_added: 2.8
  clone_pools:
    description:
      - Specifies a pool or list of pools that the virtual server uses to replicate either client-side
        or server-side traffic.
      - Typically this option is used for intrusion detection.
    suboptions:
      pool_name:
        description:
          - The pool name to which the server replicates the traffic.
          - Only pools created on Common partition or on the same partition as the virtual server can be used.
          - Referencing pool on common partition needs to be done in the full path format,
            for example, C(/Common/pool_name).
        type: str
        required: True
      context:
        description:
          - The context option for a clone pool to replicate either client-side or server-side traffic.
        type: str
        choices:
         - clientside
         - serverside
    type: list
    version_added: 2.8
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Modify Port of the Virtual Server
  bigip_virtual_server:
    state: present
    partition: Common
    name: my-virtual-server
    port: 8080
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Delete virtual server
  bigip_virtual_server:
    state: absent
    partition: Common
    name: my-virtual-server
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Add virtual server
  bigip_virtual_server:
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
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Add FastL4 virtual server
  bigip_virtual_server:
    destination: 1.1.1.1
    name: fastl4_vs
    port: 80
    profiles:
      - fastL4
    state: present
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Add iRules to the Virtual Server
  bigip_virtual_server:
    name: my-virtual-server
    irules:
      - irule1
      - irule2
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove one iRule from the Virtual Server
  bigip_virtual_server:
    name: my-virtual-server
    irules:
      - irule2
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove all iRules from the Virtual Server
  bigip_virtual_server:
    name: my-virtual-server
    irules: ""
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove pool from the Virtual Server
  bigip_virtual_server:
    name: my-virtual-server
    pool: ""
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Add metadata to virtual
  bigip_pool:
    state: absent
    name: my-pool
    partition: Common
    metadata:
      ansible: 2.4
      updated_at: 2017-12-20T17:50:46Z
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add virtual with two profiles
  bigip_pool:
    state: absent
    name: my-pool
    partition: Common
    profiles:
      - http
      - tcp
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove HTTP profile from previous virtual
  bigip_pool:
    state: absent
    name: my-pool
    partition: Common
    profiles:
      - tcp
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add the HTTP profile back to the previous virtual
  bigip_pool:
    state: absent
    name: my-pool
    partition: Common
    profiles:
      - http
      - tcp
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add virtual server with rate limit
  bigip_virtual_server:
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
    rate_limit: 400
    rate_limit_mode: destination
    rate_limit_dst_mask: 32
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Add FastL4 virtual server with clone_pools
  bigip_virtual_server:
    destination: 1.1.1.1
    name: fastl4_vs
    port: 80
    profiles:
      - fastL4
    state: present
    clone_pools:
      - pool_name: FooPool
        context: clientside
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: New description of the virtual server.
  returned: changed
  type: str
  sample: This is my description
default_persistence_profile:
  description: Default persistence profile set on the virtual server.
  returned: changed
  type: str
  sample: /Common/dest_addr
destination:
  description: Destination of the virtual server.
  returned: changed
  type: str
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
  type: str
  sample: /Common/source_addr
irules:
  description: iRules set on the virtual server.
  returned: changed
  type: list
  sample: ['/Common/irule1', '/Common/irule2']
pool:
  description: Pool that the virtual server is attached to.
  returned: changed
  type: str
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
  type: str
  sample: Automap
source:
  description: Source address, in CIDR form, set on the virtual server.
  returned: changed
  type: str
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
source_port:
  description: Specifies whether the system preserves the source port of the connection.
  returned: changed
  type: str
  sample: change
mirror:
  description: Specifies that the system mirrors connections on each member of a redundant pair.
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
  type: str
  sample: /Common/my-enforced-fw
firewall_staged_policy:
  description: The new staging firewall policy.
  returned: changed
  type: str
  sample: /Common/my-staged-fw
security_log_profiles:
  description: The new list of security log profiles.
  returned: changed
  type: list
  sample: ['/Common/profile1', '/Common/profile2']
ip_intelligence_policy:
  description: The new IP Intelligence Policy assigned to the virtual.
  returned: changed
  type: str
  sample: /Common/ip-intelligence
rate_limit:
  description: The maximum number of connections per second allowed for a virtual server.
  returned: changed
  type: int
  sample: 5000
rate_limit_src_mask:
  description: Specifies a mask, in bits, to be applied to the source address as part of the rate limiting.
  returned: changed
  type: int
  sample: 32
rate_limit_dst_mask:
  description: Specifies a mask, in bits, to be applied to the destination address as part of the rate limiting.
  returned: changed
  type: int
  sample: 32
rate_limit_mode:
  description: Sets the type of rate limiting to be used on the virtual server.
  returned: changed
  type: str
  sample: object-source
clone_pools:
  description: Pools to which virtual server copies traffic.
  returned: changed
  type: list
  sample: [{'pool_name':'/Common/Pool1', 'context': 'clientside'}]
'''
import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems
from collections import namedtuple

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import MANAGED_BY_ANNOTATION_VERSION
    from library.module_utils.network.f5.common import MANAGED_BY_ANNOTATION_MODIFIED
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import mark_managed_by
    from library.module_utils.network.f5.common import only_has_managed_metadata
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_simple_list
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import is_valid_ip_interface
    from library.module_utils.network.f5.ipaddress import ip_interface
    from library.module_utils.network.f5.ipaddress import validate_ip_v6_address
    from library.module_utils.network.f5.ipaddress import get_netmask
    from library.module_utils.network.f5.ipaddress import compress_address
    from library.module_utils.network.f5.icontrol import modules_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import MANAGED_BY_ANNOTATION_VERSION
    from ansible.module_utils.network.f5.common import MANAGED_BY_ANNOTATION_MODIFIED
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import mark_managed_by
    from ansible.module_utils.network.f5.common import only_has_managed_metadata
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_simple_list
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip_interface
    from ansible.module_utils.network.f5.ipaddress import ip_interface
    from ansible.module_utils.network.f5.ipaddress import validate_ip_v6_address
    from ansible.module_utils.network.f5.ipaddress import get_netmask
    from ansible.module_utils.network.f5.ipaddress import compress_address
    from ansible.module_utils.network.f5.icontrol import modules_provisioned


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
        'securityLogProfiles': 'security_log_profiles',
        'securityNatPolicy': 'security_nat_policy',
        'sourcePort': 'source_port',
        'ipIntelligencePolicy': 'ip_intelligence_policy',
        'rateLimit': 'rate_limit',
        'rateLimitMode': 'rate_limit_mode',
        'rateLimitDstMask': 'rate_limit_dst_mask',
        'rateLimitSrcMask': 'rate_limit_src_mask',
        'clonePools': 'clone_pools',
    }

    api_attributes = [
        'description',
        'destination',
        'disabled',
        'enabled',
        'fallbackPersistence',
        'ipProtocol',
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
        'securityNatPolicy',
        'sourcePort',
        'mirror',
        'mask',
        'ipIntelligencePolicy',
        'rateLimit',
        'rateLimitMode',
        'rateLimitDstMask',
        'rateLimitSrcMask',
        'clonePools',
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
        'ip_protocol',
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
        'security_nat_policy',
        'source_port',
        'mirror',
        'mask',
        'ip_intelligence_policy',
        'rate_limit',
        'rate_limit_mode',
        'rate_limit_src_mask',
        'rate_limit_dst_mask',
        'clone_pools',
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
        'ip_protocol',
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
        'security_nat_policy',
        'source_port',
        'mirror',
        'mask',
        'ip_intelligence_policy',
        'rate_limit',
        'rate_limit_mode',
        'rate_limit_src_mask',
        'rate_limit_dst_mask',
        'clone_pools',
    ]

    profiles_mutex = [
        'sip',
        'sipsession',
        'iiop',
        'rtsp',
        'http',
        'diameter',
        'diametersession',
        'radius',
        'ftp',
        'tftp',
        'dns',
        'pptp',
        'fix',
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

    def _format_port_for_destination(self, ip, port):
        if validate_ip_v6_address(ip):
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
        result = []
        result += self._read_diameter_profiles_from_device()
        result += self._read_sip_profiles_from_device()
        return result

    def _read_diameter_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/diameter/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [x['name'] for x in response['items']]
        return result

    def _read_sip_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/sip/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [x['name'] for x in response['items']]
        return result

    def _read_current_fastl4_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [x['name'] for x in response['items']]
        return result

    def _read_current_fasthttp_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fasthttp/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [x['name'] for x in response['items']]
        return result

    def _read_current_clientssl_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/client-ssl/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [x['name'] for x in response['items']]
        return result

    def _read_current_serverssl_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/server-ssl/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [x['name'] for x in response['items']]
        return result

    def _is_client_ssl_profile(self, profile):
        if profile['name'] in self._read_current_clientssl_profiles_from_device():
            return True
        return False

    def _is_server_ssl_profile(self, profile):
        if profile['name'] in self._read_current_serverssl_profiles_from_device():
            return True
        return False

    def _check_pool(self, item):
        pool = transform_name(name=fq_name(self.partition, item))
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            pool
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            raise F5ModuleError(
                'The specified pool {0} does not exist.'.format(pool)
            )
        return item


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
    def destination_tuple(self):
        Destination = namedtuple('Destination', ['ip', 'port', 'route_domain', 'mask'])

        # Remove the partition
        if self._values['destination'] is None:
            result = Destination(ip=None, port=None, route_domain=None, mask=None)
            return result
        destination = re.sub(r'^/[a-zA-Z0-9_.-]+/', '', self._values['destination'])
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
            result = Destination(
                ip=matches.group('ip'),
                port=port,
                route_domain=int(matches.group('route_domain')),
                mask=self.mask
            )
            return result

        pattern = r'(?P<ip>[^%]+)%(?P<route_domain>[0-9]+)'
        matches = re.search(pattern, destination)
        if matches:
            result = Destination(
                ip=matches.group('ip'),
                port=None,
                route_domain=int(matches.group('route_domain')),
                mask=self.mask
            )
            return result

        # this will match any IPV4 Address and port, no RD
        pattern = r'^(?P<ip>(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4]' \
                  r'[0-9]|25[0-5])):(?P<port>[0-9]+)'

        matches = re.search(pattern, destination)
        if matches:
            result = Destination(
                ip=matches.group('ip'),
                port=int(matches.group('port')),
                route_domain=None,
                mask=self.mask
            )
            return result

        # match standalone IPV6 address, no port
        pattern = r'^([0-9a-f]{0,4}:){2,7}(:|[0-9a-f]{1,4})$'
        matches = re.search(pattern, destination)
        if matches:
            result = Destination(
                ip=destination,
                port=None,
                route_domain=None,
                mask=self.mask
            )
            return result

        # match IPV6 address with port
        pattern = r'(?P<ip>([0-9a-f]{0,4}:){2,7}(:|[0-9a-f]{1,4}).(?P<port>[0-9]+|any))'
        matches = re.search(pattern, destination)
        if matches:
            ip = matches.group('ip').split('.')[0]
            try:
                port = int(matches.group('port'))
            except ValueError:
                # Can be a port of "any". This only happens with IPv6
                port = matches.group('port')
                if port == 'any':
                    port = 0
            result = Destination(
                ip=ip,
                port=port,
                route_domain=None,
                mask=self.mask
            )
            return result

        # this will match any alphanumeric Virtual Address and port
        pattern = r'(?P<name>^[a-zA-Z0-9_.-]+):(?P<port>[0-9]+)'
        matches = re.search(pattern, destination)
        if matches:
            result = Destination(
                ip=matches.group('name'),
                port=int(matches.group('port')),
                route_domain=None,
                mask=self.mask
            )
            return result

        # this will match any alphanumeric Virtual Address
        pattern = r'(?P<name>^[a-zA-Z0-9_.-]+)'
        matches = re.search(pattern, destination)
        if matches:
            result = Destination(
                ip=matches.group('name'),
                port=None,
                route_domain=None,
                mask=self.mask
            )
            return result

        # match IPv6 wildcard with port without RD
        pattern = r'(?P<ip>[^.]+).(?P<port>[0-9]+|any)'
        matches = re.search(pattern, destination)
        if matches:
            result = Destination(
                ip=matches.group('ip'),
                port=matches.group('port'),
                route_domain=None,
                mask=self.mask
            )
            return result

        result = Destination(ip=None, port=None, route_domain=None, mask=None)
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
        if only_has_managed_metadata(self._values['metadata']):
            return None
        result = []
        for md in self._values['metadata']:
            if md['name'] in [MANAGED_BY_ANNOTATION_VERSION, MANAGED_BY_ANNOTATION_MODIFIED]:
                continue

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

    @property
    def sec_nat_use_device_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        if 'useDevicePolicy' not in self._values['security_nat_policy']:
            return None
        if self._values['security_nat_policy']['useDevicePolicy'] == "no":
            return False
        return True

    @property
    def sec_nat_use_rd_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        if 'useRouteDomainPolicy' not in self._values['security_nat_policy']:
            return None
        if self._values['security_nat_policy']['useRouteDomainPolicy'] == "no":
            return False
        return True

    @property
    def sec_nat_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        if 'policy' not in self._values['security_nat_policy']:
            return None
        return self._values['security_nat_policy']['policy']

    @property
    def irules(self):
        if self._values['irules'] is None:
            return []
        return self._values['irules']

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        if self._values['rate_limit'] == 'disabled':
            return 0
        return int(self._values['rate_limit'])

    @property
    def clone_pools(self):
        if self._values['clone_pools'] is None:
            return None
        result = []
        for item in self._values['clone_pools']:
            pool_name = fq_name(item['partition'], item['name'])
            context = item['context']
            tmp = {
                'name': pool_name,
                'context': context
            }
            result.append(tmp)
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

    def _handle_ssl_profile_nuances(self, profile):
        if profile['name'] == 'serverssl' or self._is_server_ssl_profile(profile):
            if profile['context'] != 'serverside':
                profile['context'] = 'serverside'
        if profile['name'] == 'clientssl' or self._is_client_ssl_profile(profile):
            if profile['context'] != 'clientside':
                profile['context'] = 'clientside'
        return

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

    def _check_clone_pool_contexts(self):
        client = 0
        server = 0
        for item in self._values['clone_pools']:
            if item['context'] == 'clientside':
                client += 1
            if item['context'] == 'serverside':
                server += 1
        if client > 1 or server > 1:
            raise F5ModuleError(
                'You must specify only one clone pool for each context.'
            )

    @property
    def source(self):
        if self._values['source'] is None:
            return None
        source = self.source_tuple
        if is_valid_ip_interface(u'{0}/{1}'.format(source.ip, source.cidr)):
            if source.route_domain:
                result = '{0}%{1}/{2}'.format(source.ip, source.route_domain, source.cidr)
            else:
                result = '{0}/{1}'.format(source.ip, source.cidr)
            return result
        raise F5ModuleError(
            "The source IP address must be a valid CIDR format: address/prefix."
        )

    @property
    def source_tuple(self):
        Source = namedtuple('Source', ['ip', 'route_domain', 'cidr'])
        if self._values['source'] is None:
            result = Source(ip=None, route_domain=None, cidr=None)
            return result
        # match source with RD
        pattern = r'(?P<ip>[^%]+)%(?P<route_domain>[0-9]+)/(?P<cidr>[0-9]+)'
        matches = re.search(pattern, self._values['source'])
        if matches:
            result = Source(
                ip=matches.group('ip'),
                route_domain=matches.group('route_domain'),
                cidr=matches.group('cidr')
            )
            return result
        # match source without RD
        pattern = r'(?P<ip>[^%]+)/(?P<cidr>[0-9]+)'
        matches = re.search(pattern, self._values['source'])
        if matches:
            result = Source(
                ip=matches.group('ip'),
                route_domain=None,
                cidr=matches.group('cidr')
            )
            return result

        result = Source(ip=None, route_domain=None, cidr=None)
        return result

    @property
    def destination(self):
        pattern = r'^[a-zA-Z0-9_.-]+'
        if len(self._values['destination'].split('/')) > 1:
            addr, dud = self._values['destination'].split('/')
            if '%' in addr:
                addr = addr.split('%')[0]
        else:
            addr = self._values['destination'].split('%')[0]
        if not is_valid_ip(addr):
            matches = re.search(pattern, addr)
            if not matches:
                raise F5ModuleError(
                    "The provided destination is not a valid IP address or a Virtual Address name."
                )
        result = self._format_destination(addr, self.port, self.route_domain)
        return result

    @property
    def route_domain(self):
        if self._values['destination'] is None:
            return None
        result = None
        if len(self._values['destination'].split('/')) > 1:
            addr, dud = self._values['destination'].split('/')
            if '%' in addr:
                result = addr.split('%')
        else:
            result = self._values['destination'].split('%')
        if result and len(result) > 1:
            pattern = r'^[a-zA-Z0-9_.-]+'
            matches = re.search(pattern, result[0])
            if matches and not is_valid_ip(result[0]):
                # we need to strip RD because when using Virtual Address names the RD is not needed.
                return None
            return int(result[1])
        return None

    @property
    def destination_tuple(self):
        Destination = namedtuple('Destination', ['ip', 'port', 'route_domain', 'mask'])
        if self._values['destination'] is None:
            result = Destination(ip=None, port=None, route_domain=None, mask=None)
            return result
        addr = self._values['destination'].split("%")[0].split('/')[0]
        if is_valid_ip(addr):
            addr = compress_address(u'{0}'.format(addr))
        result = Destination(ip=addr, port=self.port, route_domain=self.route_domain, mask=self.mask)
        return result

    @property
    def mask(self):
        if self._values['destination'] is None:
            return None
        if len(self._values['destination'].split('/')) > 1:
            addr, cidr = self._values['destination'].split('/')
            if '%' in addr:
                addr = addr.split('%')[0] + '/' + cidr
            else:
                addr = self._values['destination']
        else:
            addr = self._values['destination'].split('%')[0]
        if addr in ['0.0.0.0', '0.0.0.0/any', '0.0.0.0/0']:
            return 'any'
        if addr in ['::', '::/0', '::/any6']:
            return 'any6'
        if self._values['mask'] is None:
            if is_valid_ip_interface(addr):
                return get_netmask(addr)
            else:
                return None
        return compress_address(self._values['mask'])

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        if self._values['port'] in ['*', 'any', '0']:
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
                self._handle_ssl_profile_nuances(tmp)
            else:
                full_path = fq_name(self.partition, profile)
                tmp['name'] = os.path.basename(profile)
                tmp['context'] = 'all'
                tmp['fullPath'] = full_path
                self._handle_ssl_profile_nuances(tmp)
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
    def ip_intelligence_policy(self):
        if self._values['ip_intelligence_policy'] is None:
            return None
        if self._values['ip_intelligence_policy'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['ip_intelligence_policy'])

    @property
    def security_log_profiles(self):
        if self._values['security_log_profiles'] is None:
            return None
        if len(self._values['security_log_profiles']) == 1 and self._values['security_log_profiles'][0] == '':
            return ''
        result = list(set([fq_name(self.partition, x) for x in self._values['security_log_profiles']]))
        result.sort()
        return result

    @property
    def sec_nat_use_device_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        if 'use_device_policy' not in self._values['security_nat_policy']:
            return None
        return self._values['security_nat_policy']['use_device_policy']

    @property
    def sec_nat_use_rd_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        if 'use_route_domain_policy' not in self._values['security_nat_policy']:
            return None
        return self._values['security_nat_policy']['use_route_domain_policy']

    @property
    def sec_nat_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        if 'policy' not in self._values['security_nat_policy']:
            return None
        if self._values['security_nat_policy']['policy'] == '':
            return ''
        return fq_name(self.partition, self._values['security_nat_policy']['policy'])

    @property
    def security_nat_policy(self):
        result = dict()
        if self.sec_nat_policy:
            result['policy'] = self.sec_nat_policy
        if self.sec_nat_use_device_policy is not None:
            result['use_device_policy'] = self.sec_nat_use_device_policy
        if self.sec_nat_use_rd_policy is not None:
            result['use_route_domain_policy'] = self.sec_nat_use_rd_policy
        if result:
            return result
        return None

    @property
    def mirror(self):
        result = flatten_boolean(self._values['mirror'])
        if result is None:
            return None
        if result == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        if 0 <= int(self._values['rate_limit']) <= 4294967295:
            return int(self._values['rate_limit'])
        raise F5ModuleError(
            "Valid 'rate_limit' must be in range 0 - 4294967295."
        )

    @property
    def rate_limit_src_mask(self):
        if self._values['rate_limit_src_mask'] is None:
            return None
        if 0 <= int(self._values['rate_limit_src_mask']) <= 4294967295:
            return int(self._values['rate_limit_src_mask'])
        raise F5ModuleError(
            "Valid 'rate_limit_src_mask' must be in range 0 - 4294967295."
        )

    @property
    def rate_limit_dst_mask(self):
        if self._values['rate_limit_dst_mask'] is None:
            return None
        if 0 <= int(self._values['rate_limit_dst_mask']) <= 4294967295:
            return int(self._values['rate_limit_dst_mask'])
        raise F5ModuleError(
            "Valid 'rate_limit_dst_mask' must be in range 0 - 4294967295."
        )

    @property
    def clone_pools(self):
        if self._values['clone_pools'] is None:
            return None
        if len(self._values['clone_pools']) == 1 and self._values['clone_pools'][0] in ['', []]:
            return []
        self._check_clone_pool_contexts()
        result = []
        for item in self._values['clone_pools']:
            pool_name = fq_name(self.partition, self._check_pool(item['pool_name']))
            context = item['context']
            tmp = {
                'name': pool_name,
                'context': context
            }
            result.append(tmp)
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
        if self._values['irules'] == '':
            return []
        return self._values['irules']

    @property
    def policies(self):
        if self._values['policies'] is None:
            return None
        if self._values['type'] in ['dhcp', 'reject', 'internal']:
            return None
        if self._values['policies'] == '':
            return []
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

    @property
    def security_nat_policy(self):
        if self._values['security_nat_policy'] is None:
            return None
        result = dict()
        sec = self._values['security_nat_policy']
        if 'policy' in sec:
            result['policy'] = sec['policy']
        if 'use_device_policy' in sec:
            result['useDevicePolicy'] = 'yes' if sec['use_device_policy'] else 'no'
        if 'use_route_domain_policy' in sec:
            result['useRouteDomainPolicy'] = 'yes' if sec['use_route_domain_policy'] else 'no'
        if result:
            return result
        return None


class ReportableChanges(Changes):
    @property
    def mirror(self):
        if self._values['mirror'] is None:
            return None
        elif self._values['mirror'] == 'enabled':
            return 'yes'
        return 'no'

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
        if len(self._values['policies']) == 1 and self._values['policies'][0] == '':
            return ''
        result = ['/{0}/{1}'.format(x['partition'], x['name']) for x in self._values['policies']]
        return result

    @property
    def irules(self):
        if len(self._values['irules']) == 0:
            return []
        if len(self._values['irules']) == 1 and self._values['irules'][0] == '':
            return ''
        return self._values['irules']

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

    @property
    def ip_protocol(self):
        if self._values['ip_protocol'] is None:
            return None
        try:
            int(self._values['ip_protocol'])
        except ValueError:
            return self._values['ip_protocol']

        protocol = next((x[0] for x in self.ip_protocols_map if x[1] == self._values['ip_protocol']), None)
        if protocol:
            return protocol
        return self._values['ip_protocol']


class VirtualServerValidator(object):
    def __init__(self, module=None, client=None, want=None, have=None):
        self.have = have if have else ApiParameters()
        self.want = want if want else ModuleParameters()
        self.client = client
        self.module = module

    def check_update(self):
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
            want = ip_interface(u'{0}/{1}'.format(self.want.source_tuple.ip, self.want.source_tuple.cidr))
            have = ip_interface(u'{0}'.format(self.want.destination_tuple.ip))
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
            if self.want.ip_protocol not in [6, 17, 132, 'all', 'any']:
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
        result = []
        result += self.read_dhcpv4_profiles_from_device()
        result += self.read_dhcpv6_profiles_from_device()
        return result

    def read_dhcpv4_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dhcpv4/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [fq_name(self.want.partition, x['name']) for x in response['items']]
        return result

    def read_dhcpv6_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/dhcpv6/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [fq_name(self.want.partition, x['name']) for x in response['items']]
        return result

    def read_fastl4_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fastl4/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [fq_name(self.want.partition, x['name']) for x in response['items']]
        return result

    def read_fasthttp_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/fasthttp/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [fq_name(self.want.partition, x['name']) for x in response['items']]
        return result

    def read_udp_profiles_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/profile/udp/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        result = [fq_name(self.want.partition, x['name']) for x in response['items']]
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
        if all(x is None for x in addr_tuple):
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
    def ip_intelligence_policy(self):
        if self.want.ip_intelligence_policy is None:
            return None
        if self.want.ip_intelligence_policy == '' and self.have.ip_intelligence_policy is not None:
            return ""
        if self.want.ip_intelligence_policy == '' and self.have.ip_intelligence_policy is None:
            return None
        if self.want.ip_intelligence_policy != self.have.ip_intelligence_policy:
            return self.want.ip_intelligence_policy

    @property
    def policies(self):
        if self.want.policies is None:
            return None
        if self.want.policies in [[], ''] and self.have.policies is None:
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
        if self.want.irules in [[], ''] and len(self.have.irules) == 0:
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
        elif len(self.want.metadata) == 0 and not self.want.insert_metadata:
            return None
        elif len(self.want.metadata) == 0 and self.want.insert_metadata:
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
        result = cmp_simple_list(self.want.security_log_profiles, self.have.security_log_profiles)
        return result

    @property
    def security_nat_policy(self):
        result = dict()
        if self.want.sec_nat_use_device_policy is not None:
            if self.want.sec_nat_use_device_policy != self.have.sec_nat_use_device_policy:
                result['use_device_policy'] = self.want.sec_nat_use_device_policy
        if self.want.sec_nat_use_rd_policy is not None:
            if self.want.sec_nat_use_rd_policy != self.have.sec_nat_use_rd_policy:
                result['use_route_domain_policy'] = self.want.sec_nat_use_rd_policy
        if self.want.sec_nat_policy is not None:
            if self.want.sec_nat_policy == '' and self.have.sec_nat_policy is None:
                pass
            elif self.want.sec_nat_policy != self.have.sec_nat_policy:
                result['policy'] = self.want.sec_nat_policy
        if result:
            return dict(security_nat_policy=result)

    @property
    def clone_pools(self):
        if self.want.clone_pools == [] and self.have.clone_pools:
            return self.want.clone_pools
        result = self._diff_complex_items(self.want.clone_pools, self.have.clone_pools)
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.have = ApiParameters(client=self.client)
        self.want = ModuleParameters(client=self.client, params=self.module.params)
        self.changes = UsableChanges()
        self.provisioned_modules = []

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        self.provisioned_modules = modules_provisioned(self.client)

        if state in ['present', 'enabled', 'disabled']:
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

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
        validator = VirtualServerValidator(
            module=self.module, client=self.client, have=self.have, want=self.want
        )
        validator.check_update()

        if self.want.ip_intelligence_policy is not None:
            if not any(x for x in self.provisioned_modules if x in ['afm', 'asm']):
                raise F5ModuleError(
                    "AFM must be provisioned to configure an IP Intelligence policy."
                )

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
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual/{2}".format(
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

    def create(self):
        validator = VirtualServerValidator(
            module=self.module, client=self.client, have=self.have, want=self.want
        )
        validator.check_create()

        if self.want.ip_intelligence_policy is not None:
            if not any(x for x in self.provisioned_modules if x in ['afm', 'asm']):
                raise F5ModuleError(
                    "AFM must be provisioned to configure an IP Intelligence policy."
                )

        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()

        if self.want.insert_metadata:
            # Mark the resource as managed by Ansible, this is default behavior
            params = mark_managed_by(self.module.ansible_version, params)

        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual/{2}?expandSubcollections=true".format(
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

        return ApiParameters(params=response, client=self.client)

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        if self.want.insert_metadata:
            # Mark the resource as managed by Ansible, this is default behavior
            params = mark_managed_by(self.module.ansible_version, params)

        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        # Code 404 can occur when you specify a fallback profile that does
        # not exist
        if 'code' in response and response['code'] in [400, 403, 404]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)


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
            source_port=dict(
                choices=[
                    'preserve', 'preserve-strict', 'change'
                ]
            ),
            ip_protocol=dict(
                choices=[
                    'ah', 'any', 'bna', 'esp', 'etherip', 'gre', 'icmp', 'ipencap', 'ipv6',
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
            mirror=dict(type='bool'),
            mask=dict(),
            firewall_staged_policy=dict(),
            firewall_enforced_policy=dict(),
            ip_intelligence_policy=dict(),
            security_log_profiles=dict(type='list'),
            security_nat_policy=dict(
                type='dict',
                options=dict(
                    policy=dict(),
                    use_device_policy=dict(type='bool'),
                    use_route_domain_policy=dict(type='bool')
                )
            ),
            insert_metadata=dict(
                type='bool',
                default='yes'
            ),
            rate_limit=dict(type='int'),
            rate_limit_dst_mask=dict(type='int'),
            rate_limit_src_mask=dict(type='int'),
            rate_limit_mode=dict(
                default='object',
                choices=[
                    'destination', 'object-destination', 'object-source-destination',
                    'source-destination', 'object', 'object-source', 'source'
                ]
            ),
            clone_pools=dict(
                type='list',
                options=dict(
                    pool_name=dict(required=True),
                    context=dict(
                        required=True,
                        choices=[
                            'clientside', 'serverside'
                        ]
                    )
                )
            )
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
