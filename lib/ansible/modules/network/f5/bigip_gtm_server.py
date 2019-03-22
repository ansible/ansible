#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_gtm_server
short_description: Manages F5 BIG-IP GTM servers
description:
  - Manage BIG-IP server configuration. This module is able to manipulate the server
    definitions in a BIG-IP.
version_added: 2.5
options:
  name:
    description:
      - The name of the server.
    type: str
    required: True
  state:
    description:
      - The server state. If C(absent), an attempt to delete the server will be made.
        This will only succeed if this server is not in use by a virtual server.
        C(present) creates the server and enables it. If C(enabled), enable the server
        if it exists. If C(disabled), create the server if needed, and set state to
        C(disabled).
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
  datacenter:
    description:
      - Data center the server belongs to. When creating a new GTM server, this value
        is required.
    type: str
  devices:
    description:
      - Lists the self IP addresses and translations for each device. When creating a
        new GTM server, this value is required. This list is a complex list that
        specifies a number of keys.
      - The C(name) key specifies a name for the device. The device name must
        be unique per server. This key is required.
      - The C(address) key contains an IP address, or list of IP addresses, for the
        destination server. This key is required.
      - The C(translation) key contains an IP address to translate the C(address)
        value above to. This key is optional.
      - Specifying duplicate C(name) fields is a supported means of providing device
        addresses. In this scenario, the addresses will be assigned to the C(name)'s list
        of addresses.
    type: list
  server_type:
    description:
      - Specifies the server type. The server type determines the metrics that the
        system can collect from the server. When creating a new GTM server, the default
        value C(bigip) is used.
    type: str
    choices:
      - alteon-ace-director
      - cisco-css
      - cisco-server-load-balancer
      - generic-host
      - radware-wsd
      - windows-nt-4.0
      - bigip
      - cisco-local-director-v2
      - extreme
      - generic-load-balancer
      - sun-solaris
      - cacheflow
      - cisco-local-director-v3
      - foundry-server-iron
      - netapp
      - windows-2000-server
    aliases:
      - product
  link_discovery:
    description:
      - Specifies whether the system auto-discovers the links for this server. When
        creating a new GTM server, if this parameter is not specified, the default
        value C(disabled) is used.
      - If you set this parameter to C(enabled) or C(enabled-no-delete), you must
        also ensure that the C(virtual_server_discovery) parameter is also set to
        C(enabled) or C(enabled-no-delete).
    type: str
    choices:
      - enabled
      - disabled
      - enabled-no-delete
  virtual_server_discovery:
    description:
      - Specifies whether the system auto-discovers the virtual servers for this server.
        When creating a new GTM server, if this parameter is not specified, the default
        value C(disabled) is used.
    type: str
    choices:
      - enabled
      - disabled
      - enabled-no-delete
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
  iquery_options:
    description:
      - Specifies whether the Global Traffic Manager uses this BIG-IP
        system to conduct a variety of probes before delegating traffic to it.
    suboptions:
      allow_path:
        description:
          - Specifies that the system verifies the logical network route between a data
            center server and a local DNS server.
        type: bool
      allow_service_check:
        description:
          - Specifies that the system verifies that an application on a server is running,
            by remotely running the application using an external service checker program.
        type: bool
      allow_snmp:
        description:
          - Specifies that the system checks the performance of a server running an SNMP
            agent.
        type: bool
    type: dict
    version_added: 2.7
  monitors:
    description:
      - Specifies the health monitors that the system currently uses to monitor this resource.
      - When C(availability_requirements.type) is C(require), you may only have a single monitor in the
        C(monitors) list.
    type: list
    version_added: 2.8
  availability_requirements:
    description:
      - Specifies, if you activate more than one health monitor, the number of health
        monitors that must receive successful responses in order for the link to be
        considered available.
    suboptions:
      type:
        description:
          - Monitor rule type when C(monitors) is specified.
          - When creating a new pool, if this value is not specified, the default of 'all' will be used.
        type: str
        choices:
          - all
          - at_least
          - require
      at_least:
        description:
          - Specifies the minimum number of active health monitors that must be successful
            before the link is considered up.
          - This parameter is only relevant when a C(type) of C(at_least) is used.
          - This parameter will be ignored if a type of either C(all) or C(require) is used.
        type: int
      number_of_probes:
        description:
          - Specifies the minimum number of probes that must succeed for this server to be declared up.
          - When creating a new virtual server, if this parameter is specified, then the C(number_of_probers)
            parameter must also be specified.
          - The value of this parameter should always be B(lower) than, or B(equal to), the value of C(number_of_probers).
          - This parameter is only relevant when a C(type) of C(require) is used.
          - This parameter will be ignored if a type of either C(all) or C(at_least) is used.
        type: int
      number_of_probers:
        description:
          - Specifies the number of probers that should be used when running probes.
          - When creating a new virtual server, if this parameter is specified, then the C(number_of_probes)
            parameter must also be specified.
          - The value of this parameter should always be B(higher) than, or B(equal to), the value of C(number_of_probers).
          - This parameter is only relevant when a C(type) of C(require) is used.
          - This parameter will be ignored if a type of either C(all) or C(at_least) is used.
        type: int
    type: dict
    version_added: 2.8
  prober_preference:
    description:
      - Specifies the type of prober to use to monitor this server's resources.
      - This option is ignored in C(TMOS) version C(12.x).
      - From C(TMOS) version C(13.x) and up, when prober_preference is set to C(pool)
        a C(prober_pool) parameter must be specified.
    type: str
    choices:
      - inside-datacenter
      - outside-datacenter
      - inherit
      - pool
    version_added: 2.8
  prober_fallback:
    description:
      - Specifies the type of prober to use to monitor this server's resources
        when the preferred prober is not available.
      - This option is ignored in C(TMOS) version C(12.x).
      - From C(TMOS) version C(13.x) and up, when prober_preference is set to C(pool)
        a C(prober_pool) parameter must be specified.
      - The choices are mutually exclusive with prober_preference parameter,
        with the exception of C(any-available) or C(none) option.
    type: str
    choices:
      - any
      - inside-datacenter
      - outside-datacenter
      - inherit
      - pool
      - none
    version_added: 2.8
  prober_pool:
    description:
      - Specifies the name of the prober pool to use to monitor this server's resources.
      - From C(TMOS) version C(13.x) and up, this parameter is mandatory when C(prober_preference) is set to C(pool).
      - Format of the name can be either be prepended by partition (C(/Common/foo)), or specified
        just as an object name (C(foo)).
      - In C(TMOS) version C(12.x) prober_pool can be set to empty string to revert to default setting of inherit.
    type: str
    version_added: 2.8
  limits:
    description:
      - Specifies resource thresholds or limit requirements at the pool member level.
      - When you enable one or more limit settings, the system then uses that data to take
        members in and out of service.
      - You can define limits for any or all of the limit settings. However, when a
        member does not meet the resource threshold limit requirement, the system marks
        the member as unavailable and directs load-balancing traffic to another resource.
    suboptions:
      bits_enabled:
        description:
          - Whether the bits limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      packets_enabled:
        description:
          - Whether the packets limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      connections_enabled:
        description:
          - Whether the current connections limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      cpu_enabled:
        description:
          - Whether the CPU limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      memory_enabled:
        description:
          - Whether the memory limit it enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      bits_limit:
        description:
          - Specifies the maximum allowable data throughput rate, in bits per second,
            for the member.
          - If the network traffic volume exceeds this limit, the system marks the
            member as unavailable.
        type: int
      packets_limit:
        description:
          - Specifies the maximum allowable data transfer rate, in packets per second,
            for the member.
          - If the network traffic volume exceeds this limit, the system marks the
            member as unavailable.
        type: int
      connections_limit:
        description:
          - Specifies the maximum number of concurrent connections, combined, for all of
            the member.
          - If the connections exceed this limit, the system marks the server as
            unavailable.
        type: int
      cpu_limit:
        description:
          - Specifies the percent of CPU usage.
          - If percent of CPU usage goes above the limit, the system marks the server as unavailable.
        type: int
      memory_limit:
        description:
          - Specifies the available memory required by the virtual servers on the server.
          - If available memory falls below this limit, the system marks the server as unavailable.
        type: int
    type: dict
    version_added: 2.8
extends_documentation_fragment: f5
author:
  - Robert Teller (@r-teller)
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create server "GTM_Server"
  bigip_gtm_server:
    name: GTM_Server
    datacenter: /Common/New York
    server_type: bigip
    link_discovery: disabled
    virtual_server_discovery: disabled
    devices:
      - name: server_1
        address: 1.1.1.1
      - name: server_2
        address: 2.2.2.1
        translation: 192.168.2.1
      - name: server_2
        address: 2.2.2.2
      - name: server_3
        addresses:
          - address: 3.3.3.1
          - address: 3.3.3.2
      - name: server_4
        addresses:
          - address: 4.4.4.1
            translation: 192.168.14.1
          - address: 4.4.4.2
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Create server "GTM_Server" with expanded keys
  bigip_gtm_server:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: GTM_Server
    datacenter: /Common/New York
    server_type: bigip
    link_discovery: disabled
    virtual_server_discovery: disabled
    devices:
      - name: server_1
        address: 1.1.1.1
      - name: server_2
        address: 2.2.2.1
        translation: 192.168.2.1
      - name: server_2
        address: 2.2.2.2
      - name: server_3
        addresses:
          - address: 3.3.3.1
          - address: 3.3.3.2
      - name: server_4
        addresses:
          - address: 4.4.4.1
            translation: 192.168.14.1
          - address: 4.4.4.2
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
bits_enabled:
  description: Whether the bits limit is enabled.
  returned: changed
  type: bool
  sample: yes
bits_limit:
  description: The new bits_enabled limit.
  returned: changed
  type: int
  sample: 100
connections_enabled:
  description: Whether the connections limit is enabled.
  returned: changed
  type: bool
  sample: yes
connections_limit:
  description: The new connections_limit limit.
  returned: changed
  type: int
  sample: 100
monitors:
  description: The new list of monitors for the resource.
  returned: changed
  type: list
  sample: ['/Common/monitor1', '/Common/monitor2']
link_discovery:
  description: The new C(link_discovery) configured on the remote device.
  returned: changed
  type: str
  sample: enabled
virtual_server_discovery:
  description: The new C(virtual_server_discovery) name for the trap destination.
  returned: changed
  type: str
  sample: disabled
server_type:
  description: The new type of the server.
  returned: changed
  type: str
  sample: bigip
datacenter:
  description: The new C(datacenter) which the server is part of.
  returned: changed
  type: str
  sample: datacenter01
packets_enabled:
  description: Whether the packets limit is enabled.
  returned: changed
  type: bool
  sample: yes
packets_limit:
  description: The new packets_limit limit.
  returned: changed
  type: int
  sample: 100
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import is_empty_list
    from library.module_utils.network.f5.icontrol import tmos_version
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import is_empty_list
    from ansible.module_utils.network.f5.icontrol import tmos_version
    from ansible.module_utils.network.f5.icontrol import module_provisioned

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError:
        pass


class Parameters(AnsibleF5Parameters):
    api_map = {
        'product': 'server_type',
        'virtualServerDiscovery': 'virtual_server_discovery',
        'linkDiscovery': 'link_discovery',
        'addresses': 'devices',
        'iqAllowPath': 'iquery_allow_path',
        'iqAllowServiceCheck': 'iquery_allow_service_check',
        'iqAllowSnmp': 'iquery_allow_snmp',
        'monitor': 'monitors',
        'proberPreference': 'prober_preference',
        'proberPool': 'prober_pool',
        'proberFallback': 'prober_fallback',
        'limitMaxBps': 'bits_limit',
        'limitMaxBpsStatus': 'bits_enabled',
        'limitMaxConnections': 'connections_limit',
        'limitMaxConnectionsStatus': 'connections_enabled',
        'limitMaxPps': 'packets_limit',
        'limitMaxPpsStatus': 'packets_enabled',
        'limitCpuUsage': 'cpu_limit',
        'limitCpuUsageStatus': 'cpu_enabled',
        'limitMemAvail': 'memory_limit',
        'limitMemAvailStatus': 'memory_enabled',
    }

    api_attributes = [
        'linkDiscovery',
        'virtualServerDiscovery',
        'product',
        'addresses',
        'datacenter',
        'enabled',
        'disabled',
        'iqAllowPath',
        'iqAllowServiceCheck',
        'iqAllowSnmp',
        'monitor',
        'proberPreference',
        'proberPool',
        'proberFallback',
        'limitMaxBps',
        'limitMaxBpsStatus',
        'limitMaxConnections',
        'limitMaxConnectionsStatus',
        'limitMaxPps',
        'limitMaxPpsStatus',
        'limitCpuUsage',
        'limitCpuUsageStatus',
        'limitMemAvail',
        'limitMemAvailStatus',
    ]

    updatables = [
        'link_discovery',
        'virtual_server_discovery',
        'server_type_and_devices',
        'datacenter',
        'state',
        'iquery_allow_path',
        'iquery_allow_service_check',
        'iquery_allow_snmp',
        'monitors',
        'prober_preference',
        'prober_pool',
        'prober_fallback',
        'bits_enabled',
        'bits_limit',
        'connections_enabled',
        'connections_limit',
        'packets_enabled',
        'packets_limit',
        'cpu_enabled',
        'cpu_limit',
        'memory_enabled',
        'memory_limit',
    ]

    returnables = [
        'link_discovery',
        'virtual_server_discovery',
        'server_type',
        'datacenter',
        'enabled',
        'iquery_allow_path',
        'iquery_allow_service_check',
        'iquery_allow_snmp',
        'devices',
        'monitors',
        'availability_requirements',
        'prober_preference',
        'prober_pool',
        'prober_fallback',
        'bits_enabled',
        'bits_limit',
        'connections_enabled',
        'connections_limit',
        'packets_enabled',
        'packets_limit',
        'cpu_enabled',
        'cpu_limit',
        'memory_enabled',
        'memory_limit',
    ]


class ApiParameters(Parameters):
    @property
    def devices(self):
        if self._values['devices'] is None:
            return None
        return self._values['devices']

    @property
    def server_type(self):
        if self._values['server_type'] is None:
            return None
        elif self._values['server_type'] in ['single-bigip', 'redundant-bigip']:
            return 'bigip'
        else:
            return self._values['server_type']

    @property
    def raw_server_type(self):
        if self._values['server_type'] is None:
            return None
        return self._values['server_type']

    @property
    def enabled(self):
        if self._values['enabled'] is None:
            return None
        return True

    @property
    def disabled(self):
        if self._values['disabled'] is None:
            return None
        return True

    @property
    def iquery_allow_path(self):
        if self._values['iquery_allow_path'] is None:
            return None
        elif self._values['iquery_allow_path'] == 'yes':
            return True
        return False

    @property
    def iquery_allow_service_check(self):
        if self._values['iquery_allow_service_check'] is None:
            return None
        elif self._values['iquery_allow_service_check'] == 'yes':
            return True
        return False

    @property
    def iquery_allow_snmp(self):
        if self._values['iquery_allow_snmp'] is None:
            return None
        elif self._values['iquery_allow_snmp'] == 'yes':
            return True
        return False

    @property
    def availability_requirement_type(self):
        if self._values['monitors'] is None:
            return None
        if 'min ' in self._values['monitors']:
            return 'at_least'
        elif 'require ' in self._values['monitors']:
            return 'require'
        else:
            return 'all'

    @property
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            result.sort()
            return result
        except Exception:
            return self._values['monitors']

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        if self._values['monitors'] == '/Common/bigip':
            return '/Common/bigip'
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.availability_requirement_type == 'at_least':
            monitors = ' '.join(monitors)
            result = 'min {0} of {{ {1} }}'.format(self.at_least, monitors)
        elif self.availability_requirement_type == 'require':
            monitors = ' '.join(monitors)
            result = 'require {0} from {1} {{ {2} }}'.format(self.number_of_probes, self.number_of_probers, monitors)
        else:
            result = ' and '.join(monitors).strip()
        return result

    @property
    def number_of_probes(self):
        """Returns the probes value from the monitor string.

        The monitor string for a Require monitor looks like this.

            require 1 from 2 { /Common/tcp }

        This method parses out the first of the numeric values. This values represents
        the "probes" value that can be updated in the module.

        Returns:
             int: The probes value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'require\s+(?P<probes>\d+)\s+from'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return matches.group('probes')

    @property
    def number_of_probers(self):
        """Returns the probers value from the monitor string.

        The monitor string for a Require monitor looks like this.

            require 1 from 2 { /Common/tcp }

        This method parses out the first of the numeric values. This values represents
        the "probers" value that can be updated in the module.

        Returns:
             int: The probers value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'require\s+\d+\s+from\s+(?P<probers>\d+)\s+'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return matches.group('probers')

    @property
    def at_least(self):
        """Returns the 'at least' value from the monitor string.

        The monitor string for a Require monitor looks like this.

            min 1 of { /Common/gateway_icmp }

        This method parses out the first of the numeric values. This values represents
        the "at_least" value that can be updated in the module.

        Returns:
             int: The at_least value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+(?P<least>\d+)\s+of\s+'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return matches.group('least')


class ModuleParameters(Parameters):
    def _get_limit_value(self, type):
        if self._values['limits'] is None:
            return None
        if self._values['limits'][type] is None:
            return None
        return int(self._values['limits'][type])

    def _get_limit_status(self, type):
        if self._values['limits'] is None:
            return None
        if self._values['limits'][type] is None:
            return None
        if self._values['limits'][type]:
            return 'enabled'
        return 'disabled'

    @property
    def devices(self):
        if self._values['devices'] is None:
            return None
        result = []

        for device in self._values['devices']:
            if not any(x for x in ['address', 'addresses'] if x in device):
                raise F5ModuleError(
                    "The specified device list must contain an 'address' or 'addresses' key"
                )

            if 'address' in device:
                translation = self._determine_translation(device)
                name = device['address']
                device_name = device['name']
                result.append({
                    'name': name,
                    'deviceName': device_name,
                    'translation': translation
                })
            elif 'addresses' in device:
                for address in device['addresses']:
                    translation = self._determine_translation(address)
                    name = address['address']
                    device_name = device['name']
                    result.append({
                        'name': name,
                        'deviceName': device_name,
                        'translation': translation
                    })
        return result

    @property
    def enabled(self):
        if self._values['state'] in ['present', 'enabled']:
            return True
        return False

    @property
    def datacenter(self):
        if self._values['datacenter'] is None:
            return None
        return fq_name(self.partition, self._values['datacenter'])

    def _determine_translation(self, device):
        if 'translation' not in device:
            return 'none'
        return device['translation']

    @property
    def state(self):
        if self._values['state'] == 'enabled':
            return 'present'
        return self._values['state']

    @property
    def iquery_allow_path(self):
        if self._values['iquery_options'] is None:
            return None
        elif self._values['iquery_options']['allow_path'] is None:
            return None
        return self._values['iquery_options']['allow_path']

    @property
    def iquery_allow_service_check(self):
        if self._values['iquery_options'] is None:
            return None
        elif self._values['iquery_options']['allow_service_check'] is None:
            return None
        return self._values['iquery_options']['allow_service_check']

    @property
    def iquery_allow_snmp(self):
        if self._values['iquery_options'] is None:
            return None
        elif self._values['iquery_options']['allow_snmp'] is None:
            return None
        return self._values['iquery_options']['allow_snmp']

    @property
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            result.sort()
            return result
        except Exception:
            return self._values['monitors']

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        if is_empty_list(self._values['monitors']):
            return '/Common/bigip'
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.availability_requirement_type == 'at_least':
            if self.at_least > len(self.monitors_list):
                raise F5ModuleError(
                    "The 'at_least' value must not exceed the number of 'monitors'."
                )
            monitors = ' '.join(monitors)
            result = 'min {0} of {{ {1} }}'.format(self.at_least, monitors)
        elif self.availability_requirement_type == 'require':
            monitors = ' '.join(monitors)
            if self.number_of_probes > self.number_of_probers:
                raise F5ModuleError(
                    "The 'number_of_probes' must not exceed the 'number_of_probers'."
                )
            result = 'require {0} from {1} {{ {2} }}'.format(self.number_of_probes, self.number_of_probers, monitors)
        else:
            result = ' and '.join(monitors).strip()

        return result

    def _get_availability_value(self, type):
        if self._values['availability_requirements'] is None:
            return None
        if self._values['availability_requirements'][type] is None:
            return None
        return int(self._values['availability_requirements'][type])

    @property
    def availability_requirement_type(self):
        if self._values['availability_requirements'] is None:
            return None
        return self._values['availability_requirements']['type']

    @property
    def number_of_probes(self):
        return self._get_availability_value('number_of_probes')

    @property
    def number_of_probers(self):
        return self._get_availability_value('number_of_probers')

    @property
    def at_least(self):
        return self._get_availability_value('at_least')

    @property
    def prober_pool(self):
        if self._values['prober_pool'] is None:
            return None
        if self._values['prober_pool'] == '':
            return self._values['prober_pool']
        result = fq_name(self.partition, self._values['prober_pool'])
        return result

    @property
    def prober_fallback(self):
        if self._values['prober_fallback'] == 'any':
            return 'any-available'
        return self._values['prober_fallback']

    @property
    def bits_limit(self):
        return self._get_limit_value('bits_limit')

    @property
    def packets_limit(self):
        return self._get_limit_value('packets_limit')

    @property
    def connections_limit(self):
        return self._get_limit_value('connections_limit')

    @property
    def cpu_limit(self):
        return self._get_limit_value('cpu_limit')

    @property
    def memory_limit(self):
        return self._get_limit_value('memory_limit')

    @property
    def bits_enabled(self):
        return self._get_limit_status('bits_enabled')

    @property
    def packets_enabled(self):
        return self._get_limit_status('packets_enabled')

    @property
    def connections_enabled(self):
        return self._get_limit_status('connections_enabled')

    @property
    def cpu_enabled(self):
        return self._get_limit_status('cpu_enabled')

    @property
    def memory_enabled(self):
        return self._get_limit_status('memory_enabled')


class Changes(Parameters):
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class UsableChanges(Changes):
    @property
    def monitors(self):
        monitor_string = self._values['monitors']
        if monitor_string is None:
            return None

        if '{' in monitor_string and '}':
            tmp = monitor_string.strip('}').split('{')
            monitor = ''.join(tmp).rstrip()
            return monitor

        return monitor_string

    @property
    def iquery_allow_path(self):
        if self._values['iquery_allow_path'] is None:
            return None
        elif self._values['iquery_allow_path']:
            return 'yes'
        return 'no'

    @property
    def iquery_allow_service_check(self):
        if self._values['iquery_allow_service_check'] is None:
            return None
        elif self._values['iquery_allow_service_check']:
            return 'yes'
        return 'no'

    @property
    def iquery_allow_snmp(self):
        if self._values['iquery_allow_snmp'] is None:
            return None
        elif self._values['iquery_allow_snmp']:
            return 'yes'
        return 'no'


class ReportableChanges(Changes):
    @property
    def server_type(self):
        if self._values['server_type'] in ['single-bigip', 'redundant-bigip']:
            return 'bigip'
        return self._values['server_type']

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            result.sort()
            return result
        except Exception:
            return self._values['monitors']

    @property
    def availability_requirement_type(self):
        if self._values['monitors'] is None:
            return None
        if 'min ' in self._values['monitors']:
            return 'at_least'
        elif 'require ' in self._values['monitors']:
            return 'require'
        else:
            return 'all'

    @property
    def number_of_probes(self):
        """Returns the probes value from the monitor string.

        The monitor string for a Require monitor looks like this.

            require 1 from 2 { /Common/tcp }

        This method parses out the first of the numeric values. This values represents
        the "probes" value that can be updated in the module.

        Returns:
             int: The probes value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'require\s+(?P<probes>\d+)\s+from'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return int(matches.group('probes'))

    @property
    def number_of_probers(self):
        """Returns the probers value from the monitor string.

        The monitor string for a Require monitor looks like this.

            require 1 from 2 { /Common/tcp }

        This method parses out the first of the numeric values. This values represents
        the "probers" value that can be updated in the module.

        Returns:
             int: The probers value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'require\s+\d+\s+from\s+(?P<probers>\d+)\s+'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return int(matches.group('probers'))

    @property
    def at_least(self):
        """Returns the 'at least' value from the monitor string.

        The monitor string for a Require monitor looks like this.

            min 1 of { /Common/gateway_icmp }

        This method parses out the first of the numeric values. This values represents
        the "at_least" value that can be updated in the module.

        Returns:
             int: The at_least value if found. None otherwise.
        """
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+(?P<least>\d+)\s+of\s+'
        matches = re.search(pattern, self._values['monitors'])
        if matches is None:
            return None
        return int(matches.group('least'))

    @property
    def availability_requirements(self):
        if self._values['monitors'] is None:
            return None
        result = dict()
        result['type'] = self.availability_requirement_type
        result['at_least'] = self.at_least
        result['number_of_probers'] = self.number_of_probers
        result['number_of_probes'] = self.number_of_probes
        return result

    @property
    def prober_fallback(self):
        if self._values['prober_fallback'] == 'any-available':
            return 'any'
        return self._values['prober_fallback']


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
        want = getattr(self.want, param)
        try:
            have = getattr(self.have, param)
            if want != have:
                return want
        except AttributeError:
            return want

    def _discovery_constraints(self):
        if self.want.virtual_server_discovery is None:
            virtual_server_discovery = self.have.virtual_server_discovery
        else:
            virtual_server_discovery = self.want.virtual_server_discovery

        if self.want.link_discovery is None:
            link_discovery = self.have.link_discovery
        else:
            link_discovery = self.want.link_discovery

        if link_discovery in ['enabled', 'enabled-no-delete'] and virtual_server_discovery == 'disabled':
            raise F5ModuleError(
                "Virtual server discovery must be enabled if link discovery is enabled"
            )

    def _devices_changed(self):
        if self.want.devices is None and self.want.server_type is None:
            return None
        if self.want.devices is None:
            devices = self.have.devices
        else:
            devices = self.want.devices
        if self.have.devices is None:
            have_devices = []
        else:
            have_devices = self.have.devices
        if len(devices) == 0:
            raise F5ModuleError(
                "A GTM server must have at least one device associated with it."
            )
        want = [OrderedDict(sorted(d.items())) for d in devices]
        have = [OrderedDict(sorted(d.items())) for d in have_devices]
        if want != have:
            return True
        return False

    def _server_type_changed(self):
        if self.want.server_type is None:
            self.want.update({'server_type': self.have.server_type})
        if self.want.server_type != self.have.server_type:
            return True
        return False

    @property
    def link_discovery(self):
        self._discovery_constraints()
        if self.want.link_discovery != self.have.link_discovery:
            return self.want.link_discovery

    @property
    def virtual_server_discovery(self):
        self._discovery_constraints()
        if self.want.virtual_server_discovery != self.have.virtual_server_discovery:
            return self.want.virtual_server_discovery

    def _handle_current_server_type_and_devices(self, devices_change, server_change):
        result = {}
        if devices_change:
            result['devices'] = self.want.devices
        if server_change:
            result['server_type'] = self.want.server_type
        return result

    def _handle_legacy_server_type_and_devices(self, devices_change, server_change):
        result = {}
        if server_change and devices_change:
            result['devices'] = self.want.devices
            if len(self.want.devices) > 1 and self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'redundant-bigip':
                    result['server_type'] = 'redundant-bigip'
            elif self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'single-bigip':
                    result['server_type'] = 'single-bigip'
            else:
                result['server_type'] = self.want.server_type

        elif devices_change:
            result['devices'] = self.want.devices
            if len(self.want.devices) > 1 and self.have.server_type == 'bigip':
                if self.have.raw_server_type != 'redundant-bigip':
                    result['server_type'] = 'redundant-bigip'
            elif self.have.server_type == 'bigip':
                if self.have.raw_server_type != 'single-bigip':
                    result['server_type'] = 'single-bigip'
            else:
                result['server_type'] = self.want.server_type

        elif server_change:
            if len(self.have.devices) > 1 and self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'redundant-bigip':
                    result['server_type'] = 'redundant-bigip'
            elif self.want.server_type == 'bigip':
                if self.have.raw_server_type != 'single-bigip':
                    result['server_type'] = 'single-bigip'
            else:
                result['server_type'] = self.want.server_type
        return result

    @property
    def server_type_and_devices(self):
        """Compares difference between server type and devices list

        These two parameters are linked with each other and, therefore, must be
        compared together to ensure that the correct setting is sent to BIG-IP

        :return:
        """
        devices_change = self._devices_changed()
        server_change = self._server_type_changed()
        if not devices_change and not server_change:
            return None
        tmos = tmos_version(self.client)
        if LooseVersion(tmos) >= LooseVersion('13.0.0'):
            result = self._handle_current_server_type_and_devices(
                devices_change, server_change
            )
            return result
        else:
            result = self._handle_legacy_server_type_and_devices(
                devices_change, server_change
            )
            return result

    @property
    def state(self):
        if self.want.state == 'disabled' and self.have.enabled:
            return dict(disabled=True)
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            return dict(enabled=True)

    @property
    def monitors(self):
        if self.want.monitors is None:
            return None
        if self.want.monitors == '/Common/bigip' and self.have.monitors == '/Common/bigip':
            return None
        if self.want.monitors == '/Common/bigip' and self.have.monitors is None:
            return None
        if self.want.monitors == '/Common/bigip' and len(self.have.monitors) > 0:
            return '/Common/bigip'
        if self.have.monitors is None:
            return self.want.monitors
        if self.have.monitors != self.want.monitors:
            return self.want.monitors

    @property
    def prober_pool(self):
        if self.want.prober_pool is None:
            return None
        if self.have.prober_pool is None:
            if self.want.prober_pool == '':
                return None
        if self.want.prober_pool != self.have.prober_pool:
            return self.want.prober_pool

    @property
    def prober_preference(self):
        if self.want.prober_preference is None:
            return None
        if self.want.prober_preference == self.have.prober_preference:
            return None
        if self.want.prober_preference == 'pool' and self.want.prober_pool is None:
            raise F5ModuleError(
                "A prober_pool needs to be set if prober_preference is set to 'pool'"
            )
        if self.want.prober_preference != 'pool' and self.have.prober_preference == 'pool':
            if self.want.prober_fallback != 'pool' and self.want.prober_pool != '':
                raise F5ModuleError(
                    "To change prober_preference from {0} to {1}, set prober_pool to an empty string".format(
                        self.have.prober_preference,
                        self.want.prober_preference
                    )
                )
        if self.want.prober_preference == self.want.prober_fallback:
            raise F5ModuleError(
                "Prober_preference and prober_fallback must not be equal."
            )
        if self.want.prober_preference == self.have.prober_fallback:
            raise F5ModuleError(
                "Cannot set prober_preference to {0} if prober_fallback on device is set to {1}.".format(
                    self.want.prober_preference,
                    self.have.prober_fallback
                )
            )
        if self.want.prober_preference != self.have.prober_preference:
            return self.want.prober_preference

    @property
    def prober_fallback(self):
        if self.want.prober_fallback is None:
            return None
        if self.want.prober_fallback == self.have.prober_fallback:
            return None
        if self.want.prober_fallback == 'pool' and self.want.prober_pool is None:
            raise F5ModuleError(
                "A prober_pool needs to be set if prober_fallback is set to 'pool'"
            )
        if self.want.prober_fallback != 'pool' and self.have.prober_fallback == 'pool':
            if self.want.prober_preference != 'pool' and self.want.prober_pool != '':
                raise F5ModuleError(
                    "To change prober_fallback from {0} to {1}, set prober_pool to an empty string".format(
                        self.have.prober_fallback,
                        self.want.prober_fallback
                    )
                )
        if self.want.prober_preference == self.want.prober_fallback:
            raise F5ModuleError(
                "Prober_preference and prober_fallback must not be equal."
            )
        if self.want.prober_fallback == self.have.prober_preference:
            raise F5ModuleError(
                "Cannot set prober_fallback to {0} if prober_preference on device is set to {1}.".format(
                    self.want.prober_fallback,
                    self.have.prober_preference
                )
            )
        if self.want.prober_fallback != self.have.prober_fallback:
            return self.want.prober_fallback


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.kwargs = kwargs

    def exec_module(self):
        if not module_provisioned(self.client, 'gtm'):
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
        if self.version_is_less_than('13.0.0'):
            manager = self.get_manager('v1')
        else:
            manager = self.get_manager('v2')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'v1':
            return V1Manager(**self.kwargs)
        elif type == 'v2':
            return V2Manager(**self.kwargs)

    def version_is_less_than(self, version):
        tmos = tmos_version(self.client)
        if LooseVersion(tmos) < LooseVersion(version):
            return True
        else:
            return False


class BaseManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.want.update(dict(client=self.client))
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
        diff.client = self.client
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

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state in ['present', 'enabled', 'disabled']:
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
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _check_link_discovery_requirements(self):
        if self.want.link_discovery in ['enabled', 'enabled-no-delete'] and self.want.virtual_server_discovery == 'disabled':
            raise F5ModuleError(
                "Virtual server discovery must be enabled if link discovery is enabled"
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        if self.want.state == 'disabled':
            self.want.update({'disabled': True})
        elif self.want.state in ['present', 'enabled']:
            self.want.update({'enabled': True})

        self.adjust_server_type_by_version()
        self.should_update()

        if self.want.devices is None:
            raise F5ModuleError(
                "You must provide an initial device."
            )
        self._assign_creation_defaults()
        self.handle_prober_settings()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the server")

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)
        return response['selfLink']

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}".format(
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

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.patch(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the server")
        return True

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}".format(
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


class V1Manager(BaseManager):
    def _assign_creation_defaults(self):
        if self.want.server_type is None:
            if len(self.want.devices) == 0:
                raise F5ModuleError(
                    "You must provide at least one device."
                )
            elif len(self.want.devices) == 1:
                self.want.update({'server_type': 'single-bigip'})
            else:
                self.want.update({'server_type': 'redundant-bigip'})
        if self.want.link_discovery is None:
            self.want.update({'link_discovery': 'disabled'})
        if self.want.virtual_server_discovery is None:
            self.want.update({'virtual_server_discovery': 'disabled'})
        self._check_link_discovery_requirements()

    def adjust_server_type_by_version(self):
        if len(self.want.devices) == 1 and self.want.server_type == 'bigip':
            self.want.update({'server_type': 'single-bigip'})
        if len(self.want.devices) > 1 and self.want.server_type == 'bigip':
            self.want.update({'server_type': 'redundant-bigip'})

    def update(self):
        self.have = self.read_current_from_device()
        self.handle_prober_settings()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def handle_prober_settings(self):
        if self.want.prober_preference is not None:
            self.want._values.pop('prober_preference')
        if self.want.prober_fallback is not None:
            self.want._values.pop('prober_fallback')


class V2Manager(BaseManager):
    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def _assign_creation_defaults(self):
        if self.want.server_type is None:
            self.want.update({'server_type': 'bigip'})
        if self.want.link_discovery is None:
            self.want.update({'link_discovery': 'disabled'})
        if self.want.virtual_server_discovery is None:
            self.want.update({'virtual_server_discovery': 'disabled'})
        self._check_link_discovery_requirements()

    def adjust_server_type_by_version(self):
        pass

    def handle_prober_settings(self):
        if self.want.prober_preference == 'pool' and self.want.prober_pool is None:
            raise F5ModuleError(
                "A prober_pool needs to be set if prober_preference is set to 'pool'"
            )
        if self.want.prober_preference is not None and self.want.prober_fallback is not None:
            if self.want.prober_preference == self.want.prober_fallback:
                raise F5ModuleError(
                    "The parameters for prober_preference and prober_fallback must not be the same."
                )
        if self.want.prober_fallback == 'pool' and self.want.prober_pool is None:
            raise F5ModuleError(
                "A prober_pool needs to be set if prober_fallback is set to 'pool'"
            )


class ArgumentSpec(object):
    def __init__(self):
        self.states = ['absent', 'present', 'enabled', 'disabled']
        self.server_types = [
            'alteon-ace-director',
            'cisco-css',
            'cisco-server-load-balancer',
            'generic-host',
            'radware-wsd',
            'windows-nt-4.0',
            'bigip',
            'cisco-local-director-v2',
            'extreme',
            'generic-load-balancer',
            'sun-solaris',
            'cacheflow',
            'cisco-local-director-v3',
            'foundry-server-iron',
            'netapp',
            'windows-2000-server'
        ]
        self.supports_check_mode = True
        argument_spec = dict(
            state=dict(
                default='present',
                choices=self.states,
            ),
            name=dict(required=True),
            server_type=dict(
                choices=self.server_types,
                aliases=['product']
            ),
            datacenter=dict(),
            link_discovery=dict(
                choices=['enabled', 'disabled', 'enabled-no-delete']
            ),
            virtual_server_discovery=dict(
                choices=['enabled', 'disabled', 'enabled-no-delete']
            ),
            devices=dict(
                type='list'
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            iquery_options=dict(
                type='dict',
                options=dict(
                    allow_path=dict(type='bool'),
                    allow_service_check=dict(type='bool'),
                    allow_snmp=dict(type='bool')
                )
            ),
            availability_requirements=dict(
                type='dict',
                options=dict(
                    type=dict(
                        choices=['all', 'at_least', 'require'],
                        required=True
                    ),
                    at_least=dict(type='int'),
                    number_of_probes=dict(type='int'),
                    number_of_probers=dict(type='int')
                ),
                mutually_exclusive=[
                    ['at_least', 'number_of_probes'],
                    ['at_least', 'number_of_probers'],
                ],
                required_if=[
                    ['type', 'at_least', ['at_least']],
                    ['type', 'require', ['number_of_probes', 'number_of_probers']]
                ]
            ),
            limits=dict(
                type='dict',
                options=dict(
                    bits_enabled=dict(type='bool'),
                    packets_enabled=dict(type='bool'),
                    connections_enabled=dict(type='bool'),
                    cpu_enabled=dict(type='bool'),
                    memory_enabled=dict(type='bool'),
                    bits_limit=dict(type='int'),
                    packets_limit=dict(type='int'),
                    connections_limit=dict(type='int'),
                    cpu_limit=dict(type='int'),
                    memory_limit=dict(type='int'),
                )
            ),
            monitors=dict(type='list'),
            prober_preference=dict(
                choices=['inside-datacenter', 'outside-datacenter', 'inherit', 'pool']
            ),
            prober_fallback=dict(
                choices=['inside-datacenter', 'outside-datacenter',
                         'inherit', 'pool', 'any', 'none']
            ),
            prober_pool=dict()

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
