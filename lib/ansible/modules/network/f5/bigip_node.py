#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_node
short_description: Manages F5 BIG-IP LTM nodes
description:
  - Manages F5 BIG-IP LTM nodes.
version_added: 1.4
options:
  state:
    description:
      - Specifies the current state of the node. C(enabled) (All traffic
        allowed), specifies that system sends traffic to this node regardless
        of the node's state. C(disabled) (Only persistent or active connections
        allowed), Specifies that the node can handle only persistent or
        active connections. C(offline) (Only active connections allowed),
        Specifies that the node can handle only active connections. In all
        cases except C(absent), the node will be created if it does not yet
        exist.
      - Be particularly careful about changing the status of a node whose FQDN
        cannot be resolved. These situations disable your ability to change their
        C(state) to C(disabled) or C(offline). They will remain in an
        *Unavailable - Enabled* state.
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
      - offline
    default: present
  name:
    description:
      - Specifies the name of the node.
    type: str
    required: True
  monitor_type:
    description:
      - Monitor rule type when C(monitors) is specified. When creating a new
        pool, if this value is not specified, the default of 'and_list' will
        be used.
      - Both C(single) and C(and_list) are functionally identical since BIG-IP
        considers all monitors as "a list". BIG=IP either has a list of many,
        or it has a list of one. Where they differ is in the extra guards that
        C(single) provides; namely that it only allows a single monitor.
    version_added: "1.3"
    type: str
    choices:
     - and_list
     - m_of_n
     - single
  quorum:
    description:
      - Monitor quorum value when C(monitor_type) is C(m_of_n).
    type: int
    version_added: 2.2
  monitors:
    description:
      - Specifies the health monitors that the system currently uses to
        monitor this node.
    type: list
    version_added: 2.2
  address:
    description:
      - IP address of the node. This can be either IPv4 or IPv6. When creating a
        new node, one of either C(address) or C(fqdn) must be provided. This
        parameter cannot be updated after it is set.
    type: str
    aliases:
      - ip
      - host
    version_added: 2.2
  fqdn:
    description:
      - FQDN name of the node. This can be any name that is a valid RFC 1123 DNS
        name. Therefore, the only characters that can be used are "A" to "Z",
        "a" to "z", "0" to "9", the hyphen ("-") and the period (".").
      - FQDN names must include at lease one period; delineating the host from
        the domain. ex. C(host.domain).
      - FQDN names must end with a letter or a number.
      - When creating a new node, one of either C(address) or C(fqdn) must be
        provided. This parameter cannot be updated after it is set.
    type: str
    aliases:
      - hostname
    version_added: 2.5
  fqdn_address_type:
    description:
      - Specifies whether the FQDN of the node resolves to an IPv4 or IPv6 address.
      - When creating a new node, if this parameter is not specified and C(fqdn) is
        specified, this parameter will default to C(ipv4).
      - This parameter cannot be changed after it has been set.
    type: str
    choices:
      - ipv4
      - ipv6
      - all
    version_added: 2.6
  fqdn_auto_populate:
    description:
      - Specifies whether the system automatically creates ephemeral nodes using
        the IP addresses returned by the resolution of a DNS query for a node defined
        by an FQDN.
      - When C(yes), the system generates an ephemeral node for each IP address
        returned in response to a DNS query for the FQDN of the node. Additionally,
        when a DNS response indicates the IP address of an ephemeral node no longer
        exists, the system deletes the ephemeral node.
      - When C(no), the system resolves a DNS query for the FQDN of the node with the
        single IP address associated with the FQDN.
      - When creating a new node, if this parameter is not specified and C(fqdn) is
        specified, this parameter will default to C(yes).
      - This parameter cannot be changed after it has been set.
    type: bool
    version_added: 2.6
  fqdn_up_interval:
    description:
      - Specifies the interval in which a query occurs, when the DNS server is up.
        The associated monitor attempts to probe three times, and marks the server
        down if it there is no response within the span of three times the interval
        value, in seconds.
      - This parameter accepts a value of C(ttl) to query based off of the TTL of
        the FQDN. The default TTL interval is akin to specifying C(3600).
      - When creating a new node, if this parameter is not specified and C(fqdn) is
        specified, this parameter will default to C(3600).
    type: str
    version_added: 2.6
  fqdn_down_interval:
    description:
      - Specifies the interval in which a query occurs, when the DNS server is down.
        The associated monitor continues polling as long as the DNS server is down.
      - When creating a new node, if this parameter is not specified and C(fqdn) is
        specified, this parameter will default to C(5).
    type: int
    version_added: 2.6
  description:
    description:
      - Specifies descriptive text that identifies the node.
      - You can remove a description by either specifying an empty string, or by
        specifying the special value C(none).
    type: str
  connection_limit:
    description:
      - Node connection limit. Setting this to 0 disables the limit.
    type: int
    version_added: 2.7
  rate_limit:
    description:
      - Node rate limit (connections-per-second). Setting this to 0 disables the limit.
    type: int
    version_added: 2.7
  ratio:
    description:
      - Node ratio weight. Valid values range from 1 through 100.
      - When creating a new node, if this parameter is not specified, the default of
        C(1) will be used.
    type: int
    version_added: 2.7
  dynamic_ratio:
    description:
      - The dynamic ratio number for the node. Used for dynamic ratio load balancing.
      - When creating a new node, if this parameter is not specified, the default of
        C(1) will be used.
    type: int
    version_added: 2.7
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
        type: str
        choices:
          - all
          - at_least
      at_least:
        description:
          - Specifies the minimum number of active health monitors that must be successful
            before the link is considered up.
          - This parameter is only relevant when a C(type) of C(at_least) is used.
          - This parameter will be ignored if a type of C(all) is used.
        type: int
    type: dict
    version_added: 2.8
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Add node
  bigip_node:
    host: 10.20.30.40
    name: 10.20.30.40
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add node with a single 'ping' monitor
  bigip_node:
    host: 10.20.30.40
    name: mytestserver
    monitors:
      - /Common/icmp
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Modify node description
  bigip_node:
    name: 10.20.30.40
    description: Our best server yet
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Delete node
  bigip_node:
    state: absent
    name: 10.20.30.40
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Force node offline
  bigip_node:
    state: disabled
    name: 10.20.30.40
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost

- name: Add node by their FQDN
  bigip_node:
    fqdn: foo.bar.com
    name: foobar.net
    provider:
      server: lb.mydomain.com
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
monitor_type:
  description:
    - Changed value for the monitor_type of the node.
  returned: changed and success
  type: str
  sample: m_of_n
quorum:
  description:
    - Changed value for the quorum of the node.
  returned: changed and success
  type: int
  sample: 1
monitors:
  description:
    - Changed list of monitors for the node.
  returned: changed and success
  type: list
  sample: ['icmp', 'tcp_echo']
description:
  description:
    - Changed value for the description of the node.
  returned: changed and success
  type: str
  sample: E-Commerce webserver in ORD
session:
  description:
    - Changed value for the internal session of the node.
  returned: changed and success
  type: str
  sample: user-disabled
state:
  description:
    - Changed value for the internal state of the node.
  returned: changed and success
  type: str
  sample: m_of_n
'''

import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.compat.ipaddress import ip_address
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.compat.ipaddress import ip_address


class Parameters(AnsibleF5Parameters):
    api_map = {
        'monitor': 'monitors',
        'connectionLimit': 'connection_limit',
        'rateLimit': 'rate_limit'
    }

    api_attributes = [
        'description',
        'address',
        'fqdn',
        'ratio',
        'connectionLimit',
        'rateLimit',
        'monitor',

        # Used for changing state
        #
        # user-enabled (enabled)
        # user-disabled (disabled)
        # user-disabled (offline)
        'session',

        # Used for changing state
        # user-down (offline)
        'state'
    ]

    returnables = [
        'monitors',
        'description',
        'fqdn',
        'address',
        'session',
        'state',
        'fqdn_auto_populate',
        'fqdn_address_type',
        'fqdn_up_interval',
        'fqdn_down_interval',
        'fqdn_name',
        'connection_limit',
        'ratio',
        'rate_limit',
        'availability_requirements'
    ]

    updatables = [
        'monitors',
        'description',
        'state',
        'fqdn_up_interval',
        'fqdn_down_interval',
        'tmName',
        'fqdn_auto_populate',
        'fqdn_address_type',
        'connection_limit',
        'ratio',
        'rate_limit',
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
            return result

    @property
    def rate_limit(self):
        if self._values['rate_limit'] is None:
            return None
        if self._values['rate_limit'] == 'disabled':
            return 0
        return int(self._values['rate_limit'])


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def fqdn(self):
        result = dict()
        if self._values['fqdn_up_interval'] is not None:
            result['interval'] = self._values['fqdn_up_interval']
        if self._values['fqdn_down_interval'] is not None:
            result['downInterval'] = self._values['fqdn_down_interval']
        if self._values['fqdn_auto_populate'] is not None:
            result['autopopulate'] = self._values['fqdn_auto_populate']
        if self._values['fqdn_name'] is not None:
            result['tmName'] = self._values['fqdn_name']
        if self._values['fqdn_address_type'] is not None:
            result['addressFamily'] = self._values['fqdn_address_type']
        if not result:
            return None
        return result

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


class ModuleParameters(Parameters):
    def _get_availability_value(self, type):
        if self._values['availability_requirements'] is None:
            return None
        if self._values['availability_requirements'][type] is None:
            return None
        return int(self._values['availability_requirements'][type])

    @property
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
        except Exception:
            result = self._values['monitors']
        result.sort()
        return result

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        if len(self._values['monitors']) == 1 and self._values['monitors'][0] == '':
            return '/Common/none'
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
        if self._values['monitor_type']:
            if self._values['monitor_type'] in ['single', 'and_list']:
                result = 'all'
            else:
                result = 'at_least'
            self._values['availability_requirements'] = dict(type=None)
            self._values['availability_requirements']['type'] = result
        if self._values['availability_requirements'] is None:
            return None
        return self._values['availability_requirements']['type']

    @property
    def at_least(self):
        if self._values['quorum']:
            self._values['availability_requirements'] = dict(at_least=None)
            self._values['availability_requirements']['at_least'] = self._values['quorum']
        return self._get_availability_value('at_least')

    @property
    def fqdn_up_interval(self):
        if self._values['fqdn_up_interval'] is None:
            return None
        return str(self._values['fqdn_up_interval'])

    @property
    def fqdn_down_interval(self):
        if self._values['fqdn_down_interval'] is None:
            return None
        return str(self._values['fqdn_down_interval'])

    @property
    def fqdn_auto_populate(self):
        auto_populate = self._values.get('fqdn_auto_populate', None)
        if auto_populate in BOOLEANS_TRUE:
            return 'enabled'
        elif auto_populate in BOOLEANS_FALSE:
            return 'disabled'

    @property
    def fqdn_name(self):
        return self._values.get('fqdn', None)

    @property
    def fqdn(self):
        if self._values['fqdn'] is None:
            return None
        result = dict(
            addressFamily=self._values.get('fqdn_address_type', None),
            downInterval=self._values.get('fqdn_down_interval', None),
            interval=self._values.get('fqdn_up_interval', None),
            autopopulate=None,
            tmName=self._values.get('fqdn', None)
        )
        auto_populate = self._values.get('fqdn_auto_populate', None)
        if auto_populate in BOOLEANS_TRUE:
            result['autopopulate'] = 'enabled'
        elif auto_populate in BOOLEANS_FALSE:
            result['autopopulate'] = 'disabled'
        return result

    @property
    def description(self):
        if self._values['description'] is None:
            return None
        elif self._values['description'] in ['none', '']:
            return ''
        return self._values['description']


class ApiParameters(Parameters):
    @property
    def fqdn_up_interval(self):
        if self._values['fqdn'] is None:
            return None
        if 'interval' in self._values['fqdn']:
            return str(self._values['fqdn']['interval'])

    @property
    def fqdn_down_interval(self):
        if self._values['fqdn'] is None:
            return None
        if 'downInterval' in self._values['fqdn']:
            return str(self._values['fqdn']['downInterval'])

    @property
    def fqdn_address_type(self):
        if self._values['fqdn'] is None:
            return None
        if 'addressFamily' in self._values['fqdn']:
            return str(self._values['fqdn']['addressFamily'])

    @property
    def fqdn_auto_populate(self):
        if self._values['fqdn'] is None:
            return None
        if 'autopopulate' in self._values['fqdn']:
            return str(self._values['fqdn']['autopopulate'])

    @property
    def description(self):
        if self._values['description'] in [None, 'none']:
            return None
        return self._values['description']

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
        except Exception:
            result = self._values['monitors']
        result.sort()
        return result

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
    def monitors(self):
        if self.want.monitor_type == 'single':
            if len(self.want.monitors_list) > 1:
                raise F5ModuleError(
                    "When using a 'monitor_type' of 'single', only one monitor may be provided."
                )
            elif len(self.have.monitors_list) > 1 and len(self.want.monitors_list) == 0:
                # Handle instances where there already exists many monitors, and the
                # user runs the module again specifying that the monitor_type should be
                # changed to 'single'
                raise F5ModuleError(
                    "A single monitor must be specified if more than one monitor currently exists on your pool."
                )
        if self.want.monitors is None:
            return None
        if self.want.monitors == 'default' and self.have.monitors == 'default':
            return None
        if self.want.monitors == 'default' and self.have.monitors is None:
            return None
        if self.want.monitors == '/Common/none' and self.have.monitors == '/Common/none':
            return None
        if self.want.monitors == 'default' and len(self.have.monitors) > 0:
            return 'default'
        if self.have.monitors is None:
            return self.want.monitors
        if self.have.monitors != self.want.monitors:
            return self.want.monitors

    @property
    def state(self):
        result = None
        if self.want.state in ['present', 'enabled']:
            if self.have.session not in ['user-enabled', 'monitor-enabled']:
                result = dict(
                    session='user-enabled',
                    state='user-up',
                )
        elif self.want.state == 'disabled':
            if self.have.session != 'user-disabled' or self.have.state == 'user-down':
                result = dict(
                    session='user-disabled',
                    state='user-up'
                )
        elif self.want.state == 'offline':
            if self.have.state != 'user-down':
                result = dict(
                    session='user-disabled',
                    state='user-down'
                )
        return result

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
        self.have = None
        self.want = ModuleParameters(params=self.module.params)
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

    def _announce_deprecations(self):  # lgtm [py/similar-function]
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['present', 'enabled', 'disabled', 'offline']:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except IOError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        return result

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def _check_required_creation_vars(self):
        if self.want.address is None and self.want.fqdn is None:
            raise F5ModuleError(
                "At least one of 'address' or 'fqdn' is required when creating a node"
            )
        elif self.want.address is not None and self.want.fqdn is not None:
            raise F5ModuleError(
                "Only one of 'address' or 'fqdn' can be provided when creating a node"
            )
        elif self.want.fqdn is not None:
            self.want.update(dict(address='any6'))

    def _munge_creation_state_for_device(self):
        # Modifying the state before sending to BIG-IP
        #
        # The 'state' must be set to None to exclude the values (accepted by this
        # module) from being sent to the BIG-IP because for specific Ansible states,
        # BIG-IP will consider those state values invalid.
        if self.want.state in ['present', 'enabled']:
            self.want.update(dict(
                session='user-enabled',
                state='user-up',
            ))
        elif self.want.state in 'disabled':
            self.want.update(dict(
                session='user-disabled',
                state='user-up'
            ))
        else:
            # State 'offline'
            # Offline state will result in the monitors stopping for the node
            self.want.update(dict(
                session='user-disabled',

                # only a valid state can be specified. The module's value is "offline",
                # but this is an invalid value for the BIG-IP. Therefore set it to user-down.
                state='user-down',

                # Even user-down wil not work when _creating_ a node, so we register another
                # want value (that is not sent to the API). This is checked for later to
                # determine if we have to PATCH the node to be offline.
                is_offline=True
            ))

    def create(self):
        self._check_required_creation_vars()
        self._munge_creation_state_for_device()

        if self.want.fqdn_auto_populate is None:
            self.want.update({'fqdn_auto_populate': True})
        if self.want.fqdn_address_type is None:
            self.want.update({'fqdn_address_type': 'ipv4'})
        if self.want.fqdn_up_interval is None:
            self.want.update({'fqdn_up_interval': 3600})
        if self.want.fqdn_down_interval is None:
            self.want.update({'fqdn_down_interval': 5})
        if self.want.ratio is None:
            self.want.update({'ratio': 1})
        if self.want.dynamic_ratio is None:
            self.want.update({'dynamic_ratio': 1})

        self._set_changed_options()
        if self.module.check_mode:
            return True

        # These are being set here because the ``create_on_device`` method
        # uses ``self.changes`` (to get formatting of parameters correct)
        # but these two parameters here cannot be changed and also it is
        # not easy to get the current versions of them for comparison.
        if self.want.address:
            self.changes.update({'address': self.want.address})
        if self.want.fqdn_up_interval is not None:
            self.changes.update({'fqdn_up_interval': self.want.fqdn_up_interval})
        if self.want.fqdn_down_interval is not None:
            self.changes.update({'fqdn_down_interval': self.want.fqdn_down_interval})
        if self.want.fqdn_auto_populate is not None:
            self.changes.update({'fqdn_auto_populate': self.want.fqdn_auto_populate})
        if self.want.fqdn_name is not None:
            self.changes.update({'fqdn_name': self.want.fqdn_name})
        if self.want.fqdn_address_type is not None:
            self.changes.update({'fqdn_address_type': self.want.fqdn_address_type})

        self.create_on_device()
        if not self.exists():
            raise F5ModuleError("Failed to create the node")
        # It appears that you cannot create a node in an 'offline' state, so instead
        # we update its status to offline after we create it.
        if self.want.is_offline:
            self.update_node_offline_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False

        if self.want.fqdn_auto_populate is not None:
            if self.want.fqdn_auto_populate != self.have.fqdn_auto_populate:
                raise F5ModuleError(
                    "The 'fqdn_auto_populate' parameter cannot be changed."
                )
        if self.want.fqdn_address_type is not None:
            if self.want.fqdn_address_type != self.have.fqdn_address_type:
                raise F5ModuleError(
                    "The 'fqdn_address_type' parameter cannot be changed."
                )

        if self.module.check_mode:
            return True

        self.update_on_device()
        if self.want.state == 'offline':
            self.update_node_offline_on_device()
        return True

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the node.")
        return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
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

    def exists(self):  # lgtm [py/similar-function]
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
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

    def update_node_offline_on_device(self):
        params = dict(
            session="user-disabled",
            state="user-down"
        )
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        if params:
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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/".format(
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
        self._wait_for_fqdn_checks()

    def _wait_for_fqdn_checks(self):
        while True:
            have = self.read_current_from_device()
            if have.state == 'fqdn-checking':
                time.sleep(1)
            else:
                break

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/node/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            address=dict(
                aliases=['host', 'ip']
            ),
            fqdn=dict(
                aliases=['hostname']
            ),
            description=dict(),
            state=dict(
                choices=['absent', 'present', 'enabled', 'disabled', 'offline'],
                default='present'
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            fqdn_address_type=dict(
                choices=['ipv4', 'ipv6', 'all']
            ),
            fqdn_auto_populate=dict(type='bool'),
            fqdn_up_interval=dict(),
            fqdn_down_interval=dict(type='int'),
            connection_limit=dict(type='int'),
            rate_limit=dict(type='int'),
            ratio=dict(type='int'),
            dynamic_ratio=dict(type='int'),
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


            # Deprecated parameters
            monitor_type=dict(
                choices=[
                    'and_list', 'm_of_n', 'single'
                ],
                removed_in_version=2.12,
            ),
            quorum=dict(
                type='int',
                removed_in_version=2.12,
            ),

        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['monitor_type', 'quorum', 'availability_requirements']
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
