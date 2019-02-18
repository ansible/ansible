#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# Copyright: (c) 2013, Matt Hite <mhite@hotmail.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_pool_member
short_description: Manages F5 BIG-IP LTM pool members
description:
  - Manages F5 BIG-IP LTM pool members via iControl SOAP API.
version_added: 1.4
options:
  name:
    description:
      - Name of the node to create, or re-use, when creating a new pool member.
      - This parameter is optional and, if not specified, a node name will be
        created automatically from either the specified C(address) or C(fqdn).
      - The C(enabled) state is an alias of C(present).
    version_added: 2.6
  state:
    description:
      - Pool member state.
    required: True
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
      - forced_offline
  pool:
    description:
      - Pool name. This pool must exist.
    required: True
  partition:
    description:
      - Partition
    default: Common
  address:
    description:
      - IP address of the pool member. This can be either IPv4 or IPv6. When creating a
        new pool member, one of either C(address) or C(fqdn) must be provided. This
        parameter cannot be updated after it is set.
    aliases:
      - ip
      - host
    version_added: 2.2
  fqdn:
    description:
      - FQDN name of the pool member. This can be any name that is a valid RFC 1123 DNS
        name. Therefore, the only characters that can be used are "A" to "Z",
        "a" to "z", "0" to "9", the hyphen ("-") and the period (".").
      - FQDN names must include at lease one period; delineating the host from
        the domain. ex. C(host.domain).
      - FQDN names must end with a letter or a number.
      - When creating a new pool member, one of either C(address) or C(fqdn) must be
        provided. This parameter cannot be updated after it is set.
    aliases:
      - hostname
    version_added: 2.6
  port:
    description:
      - Pool member port.
      - This value cannot be changed after it has been set.
    required: True
  connection_limit:
    description:
      - Pool member connection limit. Setting this to 0 disables the limit.
  description:
    description:
      - Pool member description.
  rate_limit:
    description:
      - Pool member rate limit (connections-per-second). Setting this to 0
        disables the limit.
  ratio:
    description:
      - Pool member ratio weight. Valid values range from 1 through 100.
        New pool members -- unless overridden with this value -- default
        to 1.
  preserve_node:
    description:
      - When state is C(absent) attempts to remove the node that the pool
        member references.
      - The node will not be removed if it is still referenced by other pool
        members. If this happens, the module will not raise an error.
      - Setting this to C(yes) disables this behavior.
    type: bool
    version_added: 2.1
  priority_group:
    description:
      - Specifies a number representing the priority group for the pool member.
      - When adding a new member, the default is 0, meaning that the member has no priority.
      - To specify a priority, you must activate priority group usage when you
        create a new pool or when adding or removing pool members. When activated,
        the system load balances traffic according to the priority group number
        assigned to the pool member.
      - The higher the number, the higher the priority, so a member with a priority
        of 3 has higher priority than a member with a priority of 1.
    version_added: 2.5
  fqdn_auto_populate:
    description:
      - Specifies whether the system automatically creates ephemeral nodes using
        the IP addresses returned by the resolution of a DNS query for a node
        defined by an FQDN.
      - When C(yes), the system generates an ephemeral node for each IP address
        returned in response to a DNS query for the FQDN of the node. Additionally,
        when a DNS response indicates the IP address of an ephemeral node no longer
        exists, the system deletes the ephemeral node.
      - When C(no), the system resolves a DNS query for the FQDN of the node
        with the single IP address associated with the FQDN.
      - When creating a new pool member, the default for this parameter is C(yes).
      - This parameter is ignored when C(reuse_nodes) is C(yes).
    type: bool
    version_added: 2.6
  reuse_nodes:
    description:
      - Reuses node definitions if requested.
    default: yes
    type: bool
    version_added: 2.6
  monitors:
    description:
      - Specifies the health monitors that the system currently uses to monitor
        this resource.
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
          - When creating a new pool, if this value is not specified, the default of
            'all' will be used.
        choices: ['all', 'at_least']
      at_least:
        description:
          - Specifies the minimum number of active health monitors that must be successful
            before the link is considered up.
          - This parameter is only relevant when a C(type) of C(at_least) is used.
          - This parameter will be ignored if a type of C(all) is used.
    version_added: 2.8
  ip_encapsulation:
    description:
      - Specifies the IP encapsulation using either IPIP (IP encapsulation within IP,
        RFC 2003) or GRE (Generic Router Encapsulation, RFC 2784) on outbound packets
        (from BIG-IP system to server-pool member).
      - When C(none), disables IP encapsulation.
      - When C(inherit), inherits IP encapsulation setting from the member's pool.
      - When any other value, Options are None, Inherit from Pool, and Member Specific.
    version_added: 2.8
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = '''
- name: Add pool member
  bigip_pool_member:
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
    description: web server
    connection_limit: 100
    rate_limit: 50
    ratio: 2
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Modify pool member ratio and description
  bigip_pool_member:
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
    ratio: 1
    description: nginx server
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Remove pool member from pool
  bigip_pool_member:
    state: absent
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Force pool member offline
  bigip_pool_member:
    state: forced_offline
    pool: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Create members with priority groups
  bigip_pool_member:
    pool: my-pool
    partition: Common
    host: "{{ item.address }}"
    name: "{{ item.name }}"
    priority_group: "{{ item.priority_group }}"
    port: 80
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
  loop:
    - host: 1.1.1.1
      name: web1
      priority_group: 4
    - host: 2.2.2.2
      name: web2
      priority_group: 3
    - host: 3.3.3.3
      name: web3
      priority_group: 2
    - host: 4.4.4.4
      name: web4
      priority_group: 1
'''

RETURN = '''
rate_limit:
  description: The new rate limit, in connections per second, of the pool member.
  returned: changed
  type: int
  sample: 100
connection_limit:
  description: The new connection limit of the pool member
  returned: changed
  type: int
  sample: 1000
description:
  description: The new description of pool member.
  returned: changed
  type: str
  sample: My pool member
ratio:
  description: The new pool member ratio weight.
  returned: changed
  type: int
  sample: 50
priority_group:
  description: The new priority group.
  returned: changed
  type: int
  sample: 3
fqdn_auto_populate:
  description: Whether FQDN auto population was set on the member or not.
  returned: changed
  type: bool
  sample: True
fqdn:
  description: The FQDN of the pool member.
  returned: changed
  type: str
  sample: foo.bar.com
address:
  description: The address of the pool member.
  returned: changed
  type: str
  sample: 1.2.3.4
monitors:
  description: The new list of monitors for the resource.
  returned: changed
  type: list
  sample: ['/Common/monitor1', '/Common/monitor2']
'''

import os
import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import exit_json
    from library.module_utils.network.f5.common import fail_json
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_valid_hostname
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import validate_ip_v6_address
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import exit_json
    from ansible.module_utils.network.f5.common import fail_json
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import is_valid_hostname
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import validate_ip_v6_address


class Parameters(AnsibleF5Parameters):
    api_map = {
        'rateLimit': 'rate_limit',
        'connectionLimit': 'connection_limit',
        'priorityGroup': 'priority_group',
        'monitor': 'monitors',
        'inheritProfile': 'inherit_profile',
        'profiles': 'ip_encapsulation',
    }

    api_attributes = [
        'rateLimit',
        'connectionLimit',
        'description',
        'ratio',
        'priorityGroup',
        'address',
        'fqdn',
        'session',
        'state',
        'monitor',

        # These two settings are for IP Encapsulation
        'inheritProfile',
        'profiles',
    ]

    returnables = [
        'rate_limit',
        'connection_limit',
        'description',
        'ratio',
        'priority_group',
        'fqdn_auto_populate',
        'session',
        'state',
        'fqdn',
        'address',
        'monitors',

        # IP Encapsulation related
        'inherit_profile',
        'ip_encapsulation',
    ]

    updatables = [
        'rate_limit',
        'connection_limit',
        'description',
        'ratio',
        'priority_group',
        'fqdn_auto_populate',
        'state',
        'monitors',
        'inherit_profile',
        'ip_encapsulation',
    ]


class ModuleParameters(Parameters):
    @property
    def full_name(self):
        delimiter = ':'
        try:
            if validate_ip_v6_address(self.full_name_dict['name']):
                delimiter = '.'
        except TypeError:
            pass
        return '{0}{1}{2}'.format(self.full_name_dict['name'], delimiter, self.port)

    @property
    def full_name_dict(self):
        if self._values['name'] is None:
            name = self._values['address'] if self._values['address'] else self._values['fqdn']
        else:
            name = self._values['name']
        return dict(
            name=name,
            port=self.port
        )

    @property
    def node_name(self):
        return self.full_name_dict['name']

    @property
    def fqdn_name(self):
        return self._values['fqdn']

    @property
    def fqdn(self):
        result = {}
        if self.fqdn_auto_populate:
            result['autopopulate'] = 'enabled'
        else:
            result['autopopulate'] = 'disabled'
        if self._values['fqdn'] is None:
            return result
        if not is_valid_hostname(self._values['fqdn']):
            raise F5ModuleError(
                "The specified 'fqdn' is not a valid hostname."
            )
        result['tmName'] = self._values['fqdn']
        return result

    @property
    def pool(self):
        return fq_name(self.want.partition, self._values['pool'])

    @property
    def port(self):
        if 0 > int(self._values['port']) or int(self._values['port']) > 65535:
            raise F5ModuleError(
                "Valid ports must be in range 0 - 65535"
            )
        return int(self._values['port'])

    @property
    def address(self):
        if self._values['address'] is None:
            return None
        elif self._values['address'] == 'any6':
            return 'any6'
        address = self._values['address'].split('%')[0]
        if is_valid_ip(address):
            return self._values['address']
        raise F5ModuleError(
            "The specified 'address' value is not a valid IP address."
        )

    @property
    def state(self):
        if self._values['state'] == 'enabled':
            return 'present'
        return self._values['state']

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
        if len(self._values['monitors']) == 1 and self._values['monitors'][0] in ['', 'none']:
            return 'default'
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.availability_requirement_type == 'at_least':
            if self.at_least > len(self.monitors_list):
                raise F5ModuleError(
                    "The 'at_least' value must not exceed the number of 'monitors'."
                )
            monitors = ' '.join(monitors)
            result = 'min {0} of {{ {1} }}'.format(self.at_least, monitors)
        else:
            result = ' and '.join(monitors).strip()
        return result

    @property
    def availability_requirement_type(self):
        if self._values['availability_requirements'] is None:
            return None
        return self._values['availability_requirements']['type']

    @property
    def at_least(self):
        return self._get_availability_value('at_least')

    @property
    def ip_encapsulation(self):
        if self._values['ip_encapsulation'] is None:
            return None
        if self._values['ip_encapsulation'] == 'inherit':
            return 'inherit'
        if self._values['ip_encapsulation'] in ['', 'none']:
            return ''
        return fq_name(self.partition, self._values['ip_encapsulation'])

    def _get_availability_value(self, type):
        if self._values['availability_requirements'] is None:
            return None
        if self._values['availability_requirements'][type] is None:
            return None
        return int(self._values['availability_requirements'][type])


class ApiParameters(Parameters):
    @property
    def ip_encapsulation(self):
        """Returns a simple name for the tunnel.

        The API stores the data like so

            "profiles": [
                {
                    "name": "gre",
                    "partition": "Common",
                    "nameReference": {
                        "link": "https://localhost/mgmt/tm/net/tunnels/gre/~Common~gre?ver=13.1.0.7"
                    }
                }
            ]

        This method returns that data as a simple profile name. For instance,

            /Common/gre

        This allows us to do comparisons of it in the Difference class and then,
        as needed, translate it back to the more complex form in the UsableChanges
        class.

        Returns:
            string: The simple form representation of the tunnel
        """
        if self._values['ip_encapsulation'] is None and self.inherit_profile == 'yes':
            return 'inherit'
        if self._values['ip_encapsulation'] is None and self.inherit_profile == 'no':
            return ''
        if self._values['ip_encapsulation'] is None:
            return None

        # There can be only one
        tunnel = self._values['ip_encapsulation'][0]

        return fq_name(tunnel['partition'], tunnel['name'])

    @property
    def inherit_profile(self):
        return flatten_boolean(self._values['inherit_profile'])

    @property
    def allow(self):
        if self._values['allow'] is None:
            return ''
        if self._values['allow'][0] == 'All':
            return 'all'
        allow = self._values['allow']
        result = list(set([str(x) for x in allow]))
        result = sorted(result)
        return result

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        if self._values['rate_limit'] == 'disabled':
            return 0
        return int(self._values['rate_limit'])

    @property
    def state(self):
        if self._values['state'] in ['user-up', 'unchecked', 'fqdn-up-no-addr', 'fqdn-up'] and self._values['session'] in ['user-enabled']:
            return 'present'
        elif self._values['state'] in ['down', 'up', 'checking'] and self._values['session'] == 'monitor-enabled':
            # monitor-enabled + checking:
            #   Monitor is checking to see state of pool member. For instance,
            #   whether it is up or down
            #
            # monitor-enabled + down:
            #   Monitor returned and determined that pool member is down.
            #
            # monitor-enabled + up
            #   Monitor returned and determined that pool member is up.
            return 'present'
        elif self._values['state'] in ['user-down'] and self._values['session'] in ['user-disabled']:
            return 'forced_offline'
        else:
            return 'disabled'

    @property
    def availability_requirement_type(self):
        if self._values['monitors'] is None:
            return None
        if 'min ' in self._values['monitors']:
            return 'at_least'
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
        if self._values['monitors'] == 'default':
            return 'default'
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.availability_requirement_type == 'at_least':
            monitors = ' '.join(monitors)
            result = 'min {0} of {{ {1} }}'.format(self.at_least, monitors)
        else:
            result = ' and '.join(monitors).strip()

        return result

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

    @property
    def fqdn_auto_populate(self):
        if self._values['fqdn'] is None:
            return None
        if 'autopopulate' in self._values['fqdn']:
            if self._values['fqdn']['autopopulate'] == 'enabled':
                return True
            return False

    @property
    def fqdn(self):
        if self._values['fqdn'] is None:
            return None
        if 'tmName' in self._values['fqdn']:
            return self._values['fqdn']['tmName']


class NodeApiParameters(Parameters):
    pass


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
    def ssl_cipher_suite(self):
        default = ':'.join(sorted(Parameters._ciphers.split(':')))
        if self._values['ssl_cipher_suite'] == default:
            return 'default'
        else:
            return self._values['ssl_cipher_suite']

    @property
    def fqdn_auto_populate(self):
        if self._values['fqdn'] is None:
            return None
        if 'autopopulate' in self._values['fqdn']:
            if self._values['fqdn']['autopopulate'] == 'enabled':
                return True
            return False

    @property
    def fqdn(self):
        if self._values['fqdn'] is None:
            return None
        if 'tmName' in self._values['fqdn']:
            return self._values['fqdn']['tmName']

    @property
    def state(self):
        if self._values['state'] in ['user-up', 'unchecked', 'fqdn-up-no-addr', 'fqdn-up'] and self._values['session'] in ['user-enabled']:
            return 'present'
        elif self._values['state'] in ['down', 'up', 'checking'] and self._values['session'] == 'monitor-enabled':
            return 'present'
        elif self._values['state'] in ['user-down'] and self._values['session'] in ['user-disabled']:
            return 'forced_offline'
        else:
            return 'disabled'

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
        else:
            return 'all'

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
    def state(self):
        if self.want.state == self.have.state:
            return None
        if self.want.state == 'forced_offline':
            return {
                'state': 'user-down',
                'session': 'user-disabled'
            }
        elif self.want.state == 'disabled':
            return {
                'state': 'user-up',
                'session': 'user-disabled'
            }
        elif self.want.state in ['present', 'enabled']:
            return {
                'state': 'user-up',
                'session': 'user-enabled'
            }

    @property
    def monitors(self):
        if self.want.monitors is None:
            return None
        if self.want.monitors == 'default' and self.have.monitors == 'default':
            return None
        if self.want.monitors == 'default' and self.have.monitors is None:
            return None
        if self.want.monitors == 'default' and len(self.have.monitors) > 0:
            return 'default'
        if self.have.monitors is None:
            return self.want.monitors
        if self.have.monitors != self.want.monitors:
            return self.want.monitors

    @property
    def ip_encapsulation(self):
        result = cmp_str_with_none(self.want.ip_encapsulation, self.have.ip_encapsulation)
        if result is None:
            return None
        if result == 'inherit':
            return dict(
                inherit_profile='enabled',
                ip_encapsulation=[]
            )
        elif result in ['', 'none']:
            return dict(
                inherit_profile='disabled',
                ip_encapsulation=[]
            )
        else:
            return dict(
                inherit_profile='disabled',
                ip_encapsulation=[
                    dict(
                        name=os.path.basename(result).strip('/'),
                        partition=os.path.dirname(result)
                    )
                ]
            )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
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

        if state in ['present', 'present', 'enabled', 'disabled', 'forced_offline']:
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

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        if not self.pool_exist():
            raise F5ModuleError('The specified pool does not exist')

        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/members/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=fq_name(self.want.partition, self.want.pool)),
            transform_name(self.want.partition, self.want.full_name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def pool_exist(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=fq_name(self.want.partition, self.want.pool))
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def node_exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.node_name)
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
        if not self.want.preserve_node:
            self.remove_node_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def _set_host_by_name(self):
        if is_valid_ip(self.want.name):
            self.want.update({
                'fqdn': None,
                'address': self.want.name
            })
        else:
            if not is_valid_hostname(self.want.name):
                raise F5ModuleError(
                    "'name' is neither a valid IP address or FQDN name."
                )
            self.want.update({
                'fqdn': self.want.name,
                'address': None
            })

    def _update_api_state_attributes(self):
        if self.want.state == 'forced_offline':
            self.want.update({
                'state': 'user-down',
                'session': 'user-disabled',
            })
        elif self.want.state == 'disabled':
            self.want.update({
                'state': 'user-up',
                'session': 'user-disabled',
            })
        elif self.want.state in ['present', 'enabled']:
            self.want.update({
                'state': 'user-up',
                'session': 'user-enabled',
            })

    def _update_address_with_existing_nodes(self):
        try:
            have = self.read_current_node_from_device(self.want.node_name)

            if self.want.fqdn_auto_populate and self.want.reuse_nodes:
                self.module.warn("'fqdn_auto_populate' is discarded in favor of the re-used node's auto-populate setting.")
            self.want.update({
                'fqdn_auto_populate': True if have.fqdn['autopopulate'] == 'enabled' else False
            })
            if 'tmName' in have.fqdn:
                self.want.update({
                    'fqdn': have.fqdn['tmName'],
                    'address': 'any6'
                })
            else:
                self.want.update({
                    'address': have.address
                })
        except Exception:
            return None

    def create(self):
        if self.want.reuse_nodes:
            self._update_address_with_existing_nodes()

        if self.want.name and not any(x for x in [self.want.address, self.want.fqdn_name]):
            self._set_host_by_name()

        if self.want.ip_encapsulation == '':
            self.changes.update({'inherit_profile': 'enabled'})
            self.changes.update({'profiles': []})
        elif self.want.ip_encapsulation:
            # Read the current list of tunnels so that IP encapsulation
            # checking can take place.
            tunnels_gre = self.read_current_tunnels_from_device('gre')
            tunnels_ipip = self.read_current_tunnels_from_device('ipip')
            tunnels = tunnels_gre + tunnels_ipip
            if self.want.ip_encapsulation not in tunnels:
                raise F5ModuleError(
                    "The specified 'ip_encapsulation' tunnel was not found on the system."
                )
            self.changes.update({'inherit_profile': 'disabled'})

        self._update_api_state_attributes()
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.full_name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/members".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=fq_name(self.want.partition, self.want.pool)),

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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/members/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=fq_name(self.want.partition, self.want.pool)),
            transform_name(self.want.partition, self.want.full_name)

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
        if self.exists():
            return self.remove()
        elif not self.want.preserve_node and self.node_exists():
            return self.remove_node_from_device()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/members/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=fq_name(self.want.partition, self.want.pool)),
            transform_name(self.want.partition, self.want.full_name)

        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def remove_node_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.node_name)
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/pool/{2}/members/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(name=fq_name(self.want.partition, self.want.pool)),
            transform_name(self.want.partition, self.want.full_name)

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

        # Read the current list of tunnels so that IP encapsulation
        # checking can take place.
        tunnels_gre = self.read_current_tunnels_from_device('gre')
        tunnels_ipip = self.read_current_tunnels_from_device('ipip')
        response['tunnels'] = tunnels_gre + tunnels_ipip

        return ApiParameters(params=response)

    def read_current_node_from_device(self, node):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, node)
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
        return NodeApiParameters(params=response)

    def read_current_tunnels_from_device(self, tunnel_type):
        uri = "https://{0}:{1}/mgmt/tm/net/tunnels/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            tunnel_type
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
        if 'items' not in response:
            return []
        return [x['fullPath'] for x in response['items']]


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            pool=dict(required=True),
            address=dict(aliases=['host', 'ip']),
            fqdn=dict(
                aliases=['hostname']
            ),
            name=dict(),
            port=dict(type='int', required=True),
            connection_limit=dict(type='int'),
            description=dict(),
            rate_limit=dict(type='int'),
            ratio=dict(type='int'),
            preserve_node=dict(type='bool'),
            priority_group=dict(type='int'),
            state=dict(
                default='present',
                choices=['absent', 'present', 'enabled', 'disabled', 'forced_offline']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            fqdn_auto_populate=dict(type='bool'),
            reuse_nodes=dict(type='bool', default=True),
            availability_requirements=dict(
                type='dict',
                options=dict(
                    type=dict(
                        choices=['all', 'at_least'],
                        required=True
                    ),
                    at_least=dict(type='int'),
                ),
                required_if=[
                    ['type', 'at_least', ['at_least']],
                ]
            ),
            monitors=dict(type='list'),
            ip_encapsulation=dict(),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['address', 'fqdn']
        ]
        self.required_one_of = [
            ['name', 'address', 'fqdn'],
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    client = F5RestClient(**module.params)

    try:
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        cleanup_tokens(client)
        exit_json(module, results, client)
    except F5ModuleError as ex:
        cleanup_tokens(client)
        fail_json(module, ex, client)


if __name__ == '__main__':
    main()
