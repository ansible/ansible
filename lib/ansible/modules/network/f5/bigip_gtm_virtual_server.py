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
module: bigip_gtm_virtual_server
short_description: Manages F5 BIG-IP GTM virtual servers
description:
  - Manages F5 BIG-IP GTM virtual servers. A GTM server can have many virtual servers
    associated with it. They are arranged in much the same way that pool members are
    to pools.
version_added: 2.6
options:
  name:
    description:
      - Specifies the name of the virtual server.
    type: str
    version_added: 2.6
  server_name:
    description:
      - Specifies the name of the server that the virtual server is associated with.
    type: str
    version_added: 2.6
  address:
    description:
      - Specifies the IP Address of the virtual server.
      - When creating a new GTM virtual server, this parameter is required.
    type: str
    version_added: 2.6
  port:
    description:
      - Specifies the service port number for the virtual server or pool member. For example,
        the HTTP service is typically port 80.
      - To specify all ports, use an C(*).
      - When creating a new GTM virtual server, if this parameter is not specified, a
        default of C(*) will be used.
    type: int
  translation_address:
    description:
      - Specifies the translation IP address for the virtual server.
      - To unset this parameter, provide an empty string (C("")) as a value.
      - When creating a new GTM virtual server, if this parameter is not specified, a
        default of C(::) will be used.
    type: str
    version_added: 2.6
  translation_port:
    description:
      - Specifies the translation port number or service name for the virtual server.
      - To specify all ports, use an C(*).
      - When creating a new GTM virtual server, if this parameter is not specified, a
        default of C(*) will be used.
    type: str
    version_added: 2.6
  availability_requirements:
    description:
      - Specifies, if you activate more than one health monitor, the number of health
        monitors that must receive successful responses in order for the link to be
        considered available.
    type: dict
    suboptions:
      type:
        description:
          - Monitor rule type when C(monitors) is specified.
          - When creating a new virtual, if this value is not specified, the default of 'all' will be used.
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
    version_added: 2.6
  monitors:
    description:
      - Specifies the health monitors that the system currently uses to monitor this resource.
      - When C(availability_requirements.type) is C(require), you may only have a single monitor in the
        C(monitors) list.
    type: list
    version_added: 2.6
  virtual_server_dependencies:
    description:
      - Specifies the virtual servers on which the current virtual server depends.
      - If any of the specified servers are unavailable, the current virtual server is also listed as unavailable.
    type: list
    suboptions:
      server:
        description:
          - Server which the dependant virtual server is part of.
        type: str
        required: True
      virtual_server:
        description:
          - Virtual server to depend on.
        type: str
        required: True
    version_added: 2.6
  link:
    description:
      - Specifies a link to assign to the server or virtual server.
    type: str
    version_added: 2.6
  limits:
    description:
      - Specifies resource thresholds or limit requirements at the server level.
      - When you enable one or more limit settings, the system then uses that data to take servers in and out
        of service.
      - You can define limits for any or all of the limit settings. However, when a server does not meet the resource
        threshold limit requirement, the system marks the entire server as unavailable and directs load-balancing
        traffic to another resource.
      - The limit settings available depend on the type of server.
    type: dict
    suboptions:
      bits_enabled:
        description:
          - Whether the bits limit is enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      packets_enabled:
        description:
          - Whether the packets limit is enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      connections_enabled:
        description:
          - Whether the current connections limit is enabled or not.
          - This parameter allows you to switch on or off the effect of the limit.
        type: bool
      bits_limit:
        description:
          - Specifies the maximum allowable data throughput rate, in bits per second, for the virtual servers on the server.
          - If the network traffic volume exceeds this limit, the system marks the server as unavailable.
        type: int
      packets_limit:
        description:
          - Specifies the maximum allowable data transfer rate, in packets per second, for the virtual servers on the server.
          - If the network traffic volume exceeds this limit, the system marks the server as unavailable.
        type: int
      connections_limit:
        description:
          - Specifies the maximum number of concurrent connections, combined, for all of the virtual servers on the server.
          - If the connections exceed this limit, the system marks the server as unavailable.
        type: int
    version_added: 2.6
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.6
  state:
    description:
      - When C(present), ensures that the resource exists.
      - When C(absent), ensures the resource is removed.
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Enable virtual server
  bigip_gtm_virtual_server:
    server_name: server1
    name: my-virtual-server
    state: enabled
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
server_name:
  description: The server name associated with the virtual server.
  returned: changed
  type: str
  sample: /Common/my-gtm-server
address:
  description: The new address of the resource.
  returned: changed
  type: str
  sample: 1.2.3.4
port:
  description: The new port of the resource.
  returned: changed
  type: int
  sample: 500
translation_address:
  description: The new translation address of the resource.
  returned: changed
  type: int
  sample: 500
translation_port:
  description: The new translation port of the resource.
  returned: changed
  type: int
  sample: 500
availability_requirements:
  description: The new availability requirement configurations for the resource.
  returned: changed
  type: dict
  sample: {'type': 'all'}
monitors:
  description: The new list of monitors for the resource.
  returned: changed
  type: list
  sample: ['/Common/monitor1', '/Common/monitor2']
virtual_server_dependencies:
  description: The new list of virtual server dependencies for the resource
  returned: changed
  type: list
  sample: ['/Common/vs1', '/Common/vs2']
link:
  description: The new link value for the resource.
  returned: changed
  type: str
  sample: /Common/my-link
limits:
  description: The new limit configurations for the resource.
  returned: changed
  type: dict
  sample: { 'bits_enabled': true, 'bits_limit': 100 }
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.compat.ipaddress import ip_address
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.compare import compare_complex_list
    from library.module_utils.network.f5.icontrol import module_provisioned
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import validate_ip_v6_address
except ImportError:
    from ansible.module_utils.compat.ipaddress import ip_address
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.compare import compare_complex_list
    from ansible.module_utils.network.f5.icontrol import module_provisioned
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import validate_ip_v6_address


class Parameters(AnsibleF5Parameters):
    api_map = {
        'limitMaxBps': 'bits_limit',
        'limitMaxBpsStatus': 'bits_enabled',
        'limitMaxConnections': 'connections_limit',
        'limitMaxConnectionsStatus': 'connections_enabled',
        'limitMaxPps': 'packets_limit',
        'limitMaxPpsStatus': 'packets_enabled',
        'translationAddress': 'translation_address',
        'translationPort': 'translation_port',
        'dependsOn': 'virtual_server_dependencies',
        'explicitLinkName': 'link',
        'monitor': 'monitors'
    }

    api_attributes = [
        'dependsOn',
        'destination',
        'disabled',
        'enabled',
        'explicitLinkName',
        'limitMaxBps',
        'limitMaxBpsStatus',
        'limitMaxConnections',
        'limitMaxConnectionsStatus',
        'limitMaxPps',
        'limitMaxPpsStatus',
        'translationAddress',
        'translationPort',
        'monitor',
    ]

    returnables = [
        'bits_enabled',
        'bits_limit',
        'connections_enabled',
        'connections_limit',
        'destination',
        'disabled',
        'enabled',
        'link',
        'monitors',
        'packets_enabled',
        'packets_limit',
        'translation_address',
        'translation_port',
        'virtual_server_dependencies',
        'availability_requirements',
    ]

    updatables = [
        'bits_enabled',
        'bits_limit',
        'connections_enabled',
        'connections_limit',
        'destination',
        'enabled',
        'link',
        'monitors',
        'packets_limit',
        'packets_enabled',
        'translation_address',
        'translation_port',
        'virtual_server_dependencies',
    ]


class ApiParameters(Parameters):
    @property
    def address(self):
        if self._values['destination'].count(':') >= 2:
            # IPv6
            parts = self._values['destination'].split('.')
        else:
            # IPv4
            parts = self._values['destination'].split(':')
        if is_valid_ip(parts[0]):
            return str(parts[0])
        raise F5ModuleError(
            "'address' parameter from API was not an IP address."
        )

    @property
    def port(self):
        if self._values['destination'].count(':') >= 2:
            # IPv6
            parts = self._values['destination'].split('.')
            return parts[1]
        # IPv4
        parts = self._values['destination'].split(':')
        return int(parts[1])

    @property
    def virtual_server_dependencies(self):
        if self._values['virtual_server_dependencies'] is None:
            return None
        results = []
        for dependency in self._values['virtual_server_dependencies']:
            parts = dependency['name'].split(':')
            result = dict(
                server=parts[0],
                virtual_server=parts[1],
            )
            results.append(result)
        if results:
            results = sorted(results, key=lambda k: k['server'])
        return results

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

    def _get_availability_value(self, type):
        if self._values['availability_requirements'] is None:
            return None
        if self._values['availability_requirements'][type] is None:
            return None
        return int(self._values['availability_requirements'][type])

    def _get_limit_status(self, type):
        if self._values['limits'] is None:
            return None
        if self._values['limits'][type] is None:
            return None
        if self._values['limits'][type]:
            return 'enabled'
        return 'disabled'

    @property
    def address(self):
        if self._values['address'] is None:
            return None
        if is_valid_ip(self._values['address']):
            ip = str(ip_address(u'{0}'.format(self._values['address'])))
            return ip
        raise F5ModuleError(
            "Specified 'address' is not an IP address."
        )

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        if self._values['port'] == '*':
            return 0
        return int(self._values['port'])

    @property
    def destination(self):
        if self.address is None:
            return None
        if self.port is None:
            return None
        if validate_ip_v6_address(self.address):
            result = '{0}.{1}'.format(self.address, self.port)
        else:
            result = '{0}:{1}'.format(self.address, self.port)
        return result

    @property
    def link(self):
        if self._values['link'] is None:
            return None
        return fq_name(self.partition, self._values['link'])

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
    def bits_enabled(self):
        return self._get_limit_status('bits_enabled')

    @property
    def packets_enabled(self):
        return self._get_limit_status('packets_enabled')

    @property
    def connections_enabled(self):
        return self._get_limit_status('connections_enabled')

    @property
    def translation_address(self):
        if self._values['translation_address'] is None:
            return None
        if self._values['translation_address'] == '':
            return 'none'
        return self._values['translation_address']

    @property
    def translation_port(self):
        if self._values['translation_port'] is None:
            return None
        if self._values['translation_port'] in ['*', ""]:
            return 0
        return int(self._values['translation_port'])

    @property
    def virtual_server_dependencies(self):
        if self._values['virtual_server_dependencies'] is None:
            return None
        results = []
        for dependency in self._values['virtual_server_dependencies']:
            result = dict(
                server=fq_name(self.partition, dependency['server']),
                virtual_server=os.path.basename(dependency['virtual_server'])
            )
            results.append(result)
        if results:
            results = sorted(results, key=lambda k: k['server'])
        return results

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
    def virtual_server_dependencies(self):
        if self._values['virtual_server_dependencies'] is None:
            return None
        results = []
        for depend in self._values['virtual_server_dependencies']:
            name = '{0}:{1}'.format(depend['server'], depend['virtual_server'])
            results.append(dict(name=name))
        return results

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


class ReportableChanges(Changes):

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
    def destination(self):
        if self.want.port is None:
            self.want.update({'port': self.have.port})
        if self.want.address is None:
            self.want.update({'address': self.have.address})
        if self.want.destination != self.have.destination:
            return self.want.destination

    @property
    def virtual_server_dependencies(self):
        if self.have.virtual_server_dependencies is None:
            return self.want.virtual_server_dependencies
        if self.want.virtual_server_dependencies is None and self.have.virtual_server_dependencies is None:
            return None
        if self.want.virtual_server_dependencies is None:
            return None
        result = compare_complex_list(self.want.virtual_server_dependencies, self.have.virtual_server_dependencies)
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
    def monitors(self):
        if self.have.monitors is None:
            return self.want.monitors
        if self.have.monitors != self.want.monitors:
            return self.want.monitors


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
        if not module_provisioned(self.client, 'gtm'):
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
        changed = False
        result = dict()
        state = self.want.state

        if state in ['present', 'enabled', 'disabled']:
            changed = self.present()
        elif state == 'absent':
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

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        if self.want.port in [None, ""]:
            self.want.update({'port': '*'})
        if self.want.translation_port in [None, ""]:
            self.want.update({'translation_port': '*'})
        if self.want.translation_address in [None, ""]:
            self.want.update({'translation_address': '::'})

        self._set_changed_options()

        if self.want.address is None:
            raise F5ModuleError(
                "You must supply an 'address' when creating a new virtual server."
            )
        if self.want.availability_requirement_type == 'require' and len(self.want.monitors_list) > 1:
            raise F5ModuleError(
                "Only one monitor may be specified when using an availability_requirement type of 'require'"
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}/virtual-servers/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.server_name),
            transform_name(name=self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}/virtual-servers/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.server_name)
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
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}/virtual-servers/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.server_name),
            transform_name(name=self.want.name)
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}/virtual-servers/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.server_name),
            transform_name(name=self.want.name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/server/{2}/virtual-servers/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.server_name),
            transform_name(name=self.want.name)
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
            server_name=dict(required=True),
            address=dict(),
            port=dict(type='int'),
            translation_address=dict(),
            translation_port=dict(),
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
            monitors=dict(type='list'),
            virtual_server_dependencies=dict(
                type='list',
                options=dict(
                    server=dict(required=True),
                    virtual_server=dict(required=True)
                )
            ),
            link=dict(),
            limits=dict(
                type='dict',
                options=dict(
                    bits_enabled=dict(type='bool'),
                    packets_enabled=dict(type='bool'),
                    connections_enabled=dict(type='bool'),
                    bits_limit=dict(type='int'),
                    packets_limit=dict(type='int'),
                    connections_limit=dict(type='int')
                )
            ),
            state=dict(
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
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
