#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

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
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
      - offline
  name:
    description:
      - Specifies the name of the node.
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
    choices: ['and_list', 'm_of_n', 'single']
  quorum:
    description:
      - Monitor quorum value when C(monitor_type) is C(m_of_n).
    version_added: 2.2
  monitors:
    description:
      - Specifies the health monitors that the system currently uses to
        monitor this node.
    version_added: 2.2
  address:
    description:
      - IP address of the node. This can be either IPv4 or IPv6. When creating a
        new node, one of either C(address) or C(fqdn) must be provided. This
        parameter cannot be updated after it is set.
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
    aliases:
      - hostname
    version_added: 2.5
  fqdn_address_type:
    description:
      - Specifies whether the FQDN of the node resolves to an IPv4 or IPv6 address.
      - When creating a new node, if this parameter is not specified and C(fqdn) is
        specified, this parameter will default to C(ipv4).
      - This parameter cannot be changed after it has been set.
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
    version_added: 2.6
  fqdn_down_interval:
    description:
      - Specifies the interval in which a query occurs, when the DNS server is down.
        The associated monitor continues polling as long as the DNS server is down.
      - When creating a new node, if this parameter is not specified and C(fqdn) is
        specified, this parameter will default to C(5).
    version_added: 2.6
  description:
    description:
      - Specifies descriptive text that identifies the node.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
notes:
  - Requires the netaddr Python package on the host. This is as easy as
    C(pip install netaddr).
requirements:
  - netaddr
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add node
  bigip_node:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    partition: Common
    host: 10.20.30.40
    name: 10.20.30.40
  delegate_to: localhost

- name: Add node with a single 'ping' monitor
  bigip_node:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    partition: Common
    host: 10.20.30.40
    name: mytestserver
    monitors:
      - /Common/icmp
  delegate_to: localhost

- name: Modify node description
  bigip_node:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    partition: Common
    name: 10.20.30.40
    description: Our best server yet
  delegate_to: localhost

- name: Delete node
  bigip_node:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    partition: Common
    name: 10.20.30.40
  delegate_to: localhost

- name: Force node offline
  bigip_node:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: disabled
    partition: Common
    name: 10.20.30.40
  delegate_to: localhost

- name: Add node by their FQDN
  bigip_node:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    partition: Common
    fqdn: foo.bar.com
    name: 10.20.30.40
  delegate_to: localhost
'''

RETURN = r'''
monitor_type:
  description:
    - Changed value for the monitor_type of the node.
  returned: changed and success
  type: string
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
  type: string
  sample: E-Commerce webserver in ORD
session:
  description:
    - Changed value for the internal session of the node.
  returned: changed and success
  type: string
  sample: user-disabled
state:
  description:
    - Changed value for the internal state of the node.
  returned: changed and success
  type: string
  sample: m_of_n
'''

import re
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE

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
        'monitor': 'monitors'
    }

    api_attributes = [
        'monitor', 'description', 'address', 'fqdn',

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
        'monitor_type', 'quorum', 'monitors', 'description', 'fqdn', 'session', 'state',
        'fqdn_auto_populate', 'fqdn_address_type', 'fqdn_up_interval',
        'fqdn_down_interval', 'fqdn_name'
    ]

    updatables = [
        'monitor_type', 'quorum', 'monitors', 'description', 'state',
        'fqdn_up_interval', 'fqdn_down_interval', 'tmName', 'fqdn_auto_populate',
        'fqdn_address_type'
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
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        try:
            result = re.findall(r'/\w+/[^\s}]+', self._values['monitors'])
            return result
        except Exception:
            return self._values['monitors']

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        monitors = [fq_name(self.partition, x) for x in self.monitors_list]
        if self.monitor_type == 'm_of_n':
            monitors = ' '.join(monitors)
            result = 'min %s of { %s }' % (self.quorum, monitors)
        else:
            result = ' and '.join(monitors).strip()
        return result

    @property
    def quorum(self):
        if self.kind == 'tm:ltm:pool:poolstate':
            if self._values['monitors'] is None:
                return None
            pattern = r'min\s+(?P<quorum>\d+)\s+of'
            matches = re.search(pattern, self._values['monitors'])
            if matches:
                quorum = matches.group('quorum')
            else:
                quorum = None
        else:
            quorum = self._values['quorum']
        try:
            if quorum is None:
                return None
            return int(quorum)
        except ValueError:
            raise F5ModuleError(
                "The specified 'quorum' must be an integer."
            )

    @property
    def monitor_type(self):
        if self.kind == 'tm:ltm:node:nodestate':
            if self._values['monitors'] is None:
                return None
            pattern = r'min\s+\d+\s+of'
            matches = re.search(pattern, self._values['monitors'])
            if matches:
                return 'm_of_n'
            else:
                return 'and_list'
        else:
            if self._values['monitor_type'] is None:
                return None
            return self._values['monitor_type']


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
        return result


class ReportableChanges(Changes):
    pass


class ModuleParameters(Parameters):
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
    def monitor_type(self):
        if self.want.monitor_type is None:
            self.want.update(dict(monitor_type=self.have.monitor_type))
        if self.want.quorum is None:
            self.want.update(dict(quorum=self.have.quorum))
        if self.want.monitor_type == 'm_of_n' and self.want.quorum is None:
            raise F5ModuleError(
                "Quorum value must be specified with monitor_type 'm_of_n'."
            )
        elif self.want.monitor_type == 'single':
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
            # Update to 'and_list' here because the above checks are all that need
            # to be done before we change the value back to what is expected by
            # BIG-IP.
            #
            # Remember that 'single' is nothing more than a fancy way of saying
            # "and_list plus some extra checks"
            self.want.update(dict(monitor_type='and_list'))
        if self.want.monitor_type != self.have.monitor_type:
            return self.want.monitor_type

    @property
    def monitors(self):
        if self.want.monitor_type is None:
            self.want.update(dict(monitor_type=self.have.monitor_type))
        if not self.want.monitors_list:
            self.want.monitors = self.have.monitors_list
        if not self.want.monitors and self.want.monitor_type is not None:
            raise F5ModuleError(
                "The 'monitors' parameter cannot be empty when 'monitor_type' parameter is specified"
            )
        if self.want.monitors != self.have.monitors:
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
    def fqdn_auto_populate(self):
        if self.want.fqdn_auto_populate is None:
            return None
        if self.want.fqdn_auto_populate != self.have.fqdn_auto_populate:
            raise F5ModuleError(
                "The 'fqdn_auto_populate' parameter cannot be changed."
            )

    @property
    def fqdn_address_type(self):
        if self.want.fqdn_address_type is None:
            return None
        if self.want.fqdn_address_type != self.have.fqdn_address_type:
            raise F5ModuleError(
                "The 'fqdn_address_type' parameter cannot be changed."
            )

    @property
    def fqdn(self):
        return None


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
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

    def _announce_deprecations(self):
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

        self._set_changed_options()
        if self.module.check_mode:
            return True

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
        resource = self.client.api.tm.ltm.nodes.node.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)

    def exists(self):
        result = self.client.api.tm.ltm.nodes.node.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_node_offline_on_device(self):
        params = dict(
            session="user-disabled",
            state="user-down"
        )
        result = self.client.api.tm.ltm.nodes.node.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def update_on_device(self):
        params = self.changes.api_params()
        result = self.client.api.tm.ltm.nodes.node.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def create_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.ltm.nodes.node.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )
        self._wait_for_fqdn_checks(resource)

    def _wait_for_fqdn_checks(self, resource):
        while True:
            if resource.state == 'fqdn-checking':
                resource.refresh()
                time.sleep(1)
            else:
                break

    def remove_from_device(self):
        result = self.client.api.tm.ltm.nodes.node.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if result:
            result.delete()


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
            monitor_type=dict(
                choices=[
                    'and_list', 'm_of_n', 'single'
                ]
            ),
            quorum=dict(type='int'),
            monitors=dict(type='list'),
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
            fqdn_down_interval=dict(type='int')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
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
