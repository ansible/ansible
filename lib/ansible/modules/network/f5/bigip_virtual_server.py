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
version_added: "2.1"
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
    required: True
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
  profiles:
    description:
      - List of profiles (HTTP, ClientSSL, ServerSSL, etc) to apply to both sides
        of the connection (client-side and server-side).
      - If you only want to apply a particular profile to the client-side of
        the connection, specify C(client-side) for the profile's C(context).
      - If you only want to apply a particular profile to the server-side of
        the connection, specify C(server-side) for the profile's C(context).
      - If C(context) is not provided, it will default to C(all).
    suboptions:
      name:
        description:
          - Name of the profile.
          - If this is not specified, then it is assumed that the profile item is
            only a name of a profile.
          - This must be specified if a context is specified.
        required: false
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
    version_added: "2.2"
    description:
      - List of rules to be applied in priority order.
      - If you want to remove existing iRules, specify a single empty value; C("").
        See the documentation for an example.
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
  policies:
    description:
      - Specifies the policies for the virtual server
    aliases:
      - all_policies
  snat:
    description:
      - Source network address policy.
    required: false
    choices:
      - None
      - Automap
      - Name of a SNAT pool (eg "/Common/snat_pool_name") to enable SNAT
        with the specific pool
  default_persistence_profile:
    description:
      - Default Profile which manages the session persistence.
      - If you want to remove the existing default persistence profile, specify an
        empty value; C(""). See the documentation for an example.
  description:
    description:
      - Virtual server description.
  fallback_persistence_profile:
    description:
      - Specifies the persistence profile you want the system to use if it
        cannot use the specified default persistence profile.
      - If you want to remove the existing fallback persistence profile, specify an
        empty value; C(""). See the documentation for an example.
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
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.six import iteritems
from collections import namedtuple

try:
    # Sideband repository used for dev
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fqdn_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
    HAS_DEVEL_IMPORTS = True
except ImportError:
    # Upstream Ansible
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fqdn_name
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
        'rules': 'irules'
    }

    api_attributes = [
        'description',
        'destination',
        'disabled',
        'enabled',
        'fallbackPersistence',
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
    ]

    updatables = [
        'description',
        'default_persistence_profile',
        'destination',
        'disabled_vlans',
        'enabled',
        'enabled_vlans',
        'fallback_persistence_profile',
        'irules',
        'metadata',
        'pool',
        'policies',
        'port',
        'profiles',
        'snat',
        'source'
    ]

    returnables = [
        'description',
        'default_persistence_profile',
        'destination',
        'disabled',
        'disabled_vlans',
        'enabled',
        'enabled_vlans',
        'fallback_persistence_profile',
        'irules',
        'metadata',
        'pool',
        'policies',
        'port',
        'profiles',
        'snat',
        'source',
        'vlans',
        'vlans_enabled',
        'vlans_disabled'
    ]

    profiles_mutex = [
        'sip', 'sipsession', 'iiop', 'rtsp', 'http', 'diameter',
        'diametersession', 'radius', 'ftp', 'tftp', 'dns', 'pptp', 'fix'
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            try:
                result[returnable] = getattr(self, returnable)
            except Exception as ex:
                pass
        result = self._filter_params(result)
        return result

    def _fqdn_name(self, value):
        if value is not None and not value.startswith('/'):
            return '/{0}/{1}'.format(self.partition, value)
        return value

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
                    self._fqdn_name(address)
                )
            else:
                result = '{0}%{1}'.format(
                    self._fqdn_name(address),
                    route_domain
                )
        else:
            port = self._format_port_for_destination(address, port)
            if route_domain is None:
                result = '{0}{1}'.format(
                    self._fqdn_name(address),
                    port
                )
            else:
                result = '{0}%{1}{2}'.format(
                    self._fqdn_name(address),
                    route_domain,
                    port
                )
        return result


class ApiParameters(Parameters):
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
        destination = self.destination_tuple
        self._values['route_domain'] = destination.route_domain
        return destination.route_domain

    @property
    def profiles(self):
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
        if self._values['default_persistence_profile'] is None:
            return None
        # These persistence profiles are always lists when we get them
        # from the REST API even though there can only be one. We'll
        # make it a list again when we get to the Difference engine.
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


class ModuleParameters(Parameters):
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
        self._check_port()
        return int(self._values['port'])

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
    def irules(self):
        results = []
        if self._values['irules'] is None:
            return None
        if len(self._values['irules']) == 1 and self._values['irules'][0] == '':
            return ''
        for irule in self._values['irules']:
            result = self._fqdn_name(irule)
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
                tmp['fullPath'] = self._fqdn_name(tmp['name'])
                self._handle_clientssl_profile_nuances(tmp)
            else:
                tmp['name'] = profile
                tmp['context'] = 'all'
                tmp['fullPath'] = self._fqdn_name(tmp['name'])
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
        policies = [self._fqdn_name(p) for p in self._values['policies']]
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
        return self._fqdn_name(self._values['pool'])

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
            result = [self._fqdn_name('all')]
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
        results = list(set([self._fqdn_name(x) for x in self._values['enabled_vlans']]))
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
        results = list(set([self._fqdn_name(x) for x in self._values['disabled_vlans']]))
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
        snat_pool = self._fqdn_name(self._values['snat'])
        return dict(pool=snat_pool, type='snat')

    @property
    def default_persistence_profile(self):
        if self._values['default_persistence_profile'] is None:
            return None
        if self._values['default_persistence_profile'] == '':
            return ''
        profile = self._fqdn_name(self._values['default_persistence_profile'])
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
        result = self._fqdn_name(self._values['fallback_persistence_profile'])
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


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def vlans(self):
        if self._values['vlans'] is None:
            return None
        elif len(self._values['vlans']) == 0:
            return []
        elif any(x for x in self._values['vlans'] if x.lower() in ['/common/all', 'all']):
            return []
        return self._values['vlans']


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
            return self.want._fqdn_name(want)

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
                have = set([x for x in have if x[0] != 'tcp'])
            if not any(x[0] == 'udp' for x in want):
                have = set([x for x in have if x[0] != 'udp'])
            if not any(x[0] == 'sctp' for x in want):
                have = set([x for x in have if x[0] != 'sctp'])
            want = set([(p[2], p[1]) for p in want])
            have = set([(p[2], p[1]) for p in have])
            if want != have:
                return self.want.profiles

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
            return [self.want.default_persistence_profile]
        w_name = self.want.default_persistence_profile.get('name', None)
        w_partition = self.want.default_persistence_profile.get('partition', None)
        h_name = self.have.default_persistence_profile.get('name', None)
        h_partition = self.have.default_persistence_profile.get('partition', None)
        if w_name != h_name or w_partition != h_partition:
            return [self.want.default_persistence_profile]

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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = ApiParameters()
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
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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
        required_resources = ['destination', 'port']

        self._set_changed_options()
        # This must be changed back to a list to make a valid REST API
        # value. The module manipulates this as a normal dictionary
        if self.want.default_persistence_profile is not None:
            self.want.update({'default_persistence_profile': [self.want.default_persistence_profile]})

        if self.want.destination is None:
            raise F5ModuleError(
                "'destination' must be specified when creating a virtual server"
            )
        if all(getattr(self.want, v) is None for v in required_resources):
            raise F5ModuleError(
                "You must specify both of " + ', '.join(required_resources)
            )
        if self.want.enabled_vlans is not None:
            if any(x for x in self.want.enabled_vlans if x.lower() in ['/common/all', 'all']):
                self.want.update(
                    dict(
                        enabled_vlans=[],
                        vlans_disabled=True,
                        vlans_enabled=False
                    )
                )
        if self.want.source and self.want.destination:
            want = netaddr.IPNetwork(self.want.source)
            have = netaddr.IPNetwork(self.want.destination_tuple.ip)
            if want.version != have.version:
                raise F5ModuleError(
                    "The source and destination addresses for the virtual server must be be the same type (IPv4 or IPv6)."
                )
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
        result = ApiParameters(params=params)
        return result

    def create_on_device(self):
        params = self.want.api_params()
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
            port=dict(
                type='int'
            ),
            profiles=dict(
                type='list',
                aliases=['all_profiles'],
                options=dict(
                    name=dict(required=False),
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
