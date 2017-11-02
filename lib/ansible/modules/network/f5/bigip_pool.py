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
module: bigip_pool
short_description: Manages F5 BIG-IP LTM pools
description:
  - Manages F5 BIG-IP LTM pools via iControl REST API.
version_added: 1.2
options:
  description:
    description:
      - Specifies descriptive text that identifies the pool.
    version_added: "2.3"
  name:
    description:
      - Pool name
    required: True
    aliases:
      - pool
  lb_method:
    description:
      - Load balancing method. When creating a new pool, if this value is not
        specified, the default of C(round-robin) will be used.
    version_added: "1.3"
    choices:
      - dynamic-ratio-member
      - dynamic-ratio-node
      - fastest-app-response
      - fastest-node
      - least-connections-member
      - least-connections-node
      - least-sessions
      - observed-member
      - observed-node
      - predictive-member
      - predictive-node
      - ratio-least-connections-member
      - ratio-least-connections-node
      - ratio-member
      - ratio-node
      - ratio-session
      - round-robin
      - weighted-least-connections-member
      - weighted-least-connections-nod
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
    version_added: "1.3"
  monitors:
    description:
      - Monitor template name list. If the partition is not provided as part of
        the monitor name, then the C(partition) option will be used instead.
    version_added: "1.3"
  slow_ramp_time:
    description:
      - Sets the ramp-up time (in seconds) to gradually ramp up the load on
        newly added or freshly detected up pool members.
    version_added: "1.3"
  reselect_tries:
    description:
      - Sets the number of times the system tries to contact a pool member
        after a passive failure.
    version_added: "2.2"
  service_down_action:
    description:
      - Sets the action to take when node goes down in pool.
    version_added: "1.3"
    choices:
      - none
      - reset
      - drop
      - reselect
  host:
    description:
      - Pool member IP.
      - Deprecated in 2.4. Use the C(bigip_pool_member) module instead.
    aliases:
      - address
  port:
    description:
      - Pool member port.
      - Deprecated in 2.4. Use the C(bigip_pool_member) module instead.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
notes:
  - Requires BIG-IP software version >= 12.
  - F5 developed module 'F5-SDK' required (https://github.com/F5Networks/f5-common-python).
  - Best run as a local_action in your playbook.
requirements:
  - f5-sdk
  - Python >= 2.7
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create pool
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    lb_method: least_connection_member
    slow_ramp_time: 120
  delegate_to: localhost

- name: Modify load balancer method
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    lb_method: round_robin
  delegate_to: localhost

- name: Add pool member
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
  delegate_to: localhost

- name: Set a single monitor (with enforcement)
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    monitor_type: single
    monitors:
      - http
  delegate_to: localhost

- name: Set a single monitor (without enforcement)
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    monitors:
      - http
  delegate_to: localhost

- name: Set multiple monitors (all must succeed)
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    monitor_type: and_list
    monitors:
      - http
      - tcp
  delegate_to: localhost

- name: Set multiple monitors (at least 1 must succeed)
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    name: my-pool
    partition: Common
    monitor_type: m_of_n
    quorum: 1
    monitors:
      - http
      - tcp
  delegate_to: localhost

- name: Remove pool member from pool
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    name: my-pool
    partition: Common
    host: "{{ ansible_default_ipv4['address'] }}"
    port: 80
  delegate_to: localhost

- name: Delete pool
  bigip_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    name: my-pool
    partition: Common
  delegate_to: localhost
'''

RETURN = r'''
monitor_type:
  description: The contact that was set on the datacenter.
  returned: changed
  type: string
  sample: admin@root.local
quorum:
  description: The quorum that was set on the pool.
  returned: changed
  type: int
  sample: 2
monitors:
  description: Monitors set on the pool.
  returned: changed
  type: list
  sample: ['/Common/http', '/Common/gateway_icmp']
service_down_action:
  description: Service down action that is set on the pool.
  returned: changed
  type: string
  sample: reset
description:
  description: Description set on the pool.
  returned: changed
  type: string
  sample: Pool of web servers
lb_method:
  description: The LB method set for the pool.
  returned: changed
  type: string
  sample: round-robin
host:
  description: IP of pool member included in pool.
  returned: changed
  type: string
  sample: 10.10.10.10
port:
  description: Port of pool member included in pool.
  returned: changed
  type: int
  sample: 80
slow_ramp_time:
  description: The new value that is set for the slow ramp-up time.
  returned: changed
  type: int
  sample: 500
reselect_tries:
  description: The new value that is set for the number of tries to contact member.
  returned: changed
  type: int
  sample: 10
'''

import re

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from netaddr import IPAddress, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'loadBalancingMode': 'lb_method',
        'slowRampTime': 'slow_ramp_time',
        'reselectTries': 'reselect_tries',
        'serviceDownAction': 'service_down_action',
        'monitor': 'monitors'
    }

    api_attributes = [
        'description', 'name', 'loadBalancingMode', 'monitor', 'slowRampTime',
        'reselectTries', 'serviceDownAction'
    ]

    returnables = [
        'monitor_type', 'quorum', 'monitors', 'service_down_action',
        'description', 'lb_method', 'host', 'port', 'slow_ramp_time',
        'reselect_tries', 'monitor', 'member_name', 'name', 'partition'
    ]

    updatables = [
        'monitor_type', 'quorum', 'monitors', 'service_down_action',
        'description', 'lb_method', 'slow_ramp_time', 'reselect_tries',
        'host', 'port'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        if params:
            self.update(params=params)
        self._values['__warnings'] = []

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    @property
    def lb_method(self):
        lb_map = {
            'ratio_node_address': 'ratio-node',
            'dynamic_ratio': 'dynamic-ratio-node',
            'least_connection_member': 'least-connections-member',
            'least_connection_node_address': 'least-connections-node',
            'fastest_node_address': 'fastest-node',
            'observed_node_address': 'observed-node',
            'predictive_node_address': 'predictive-node',
            'weighted_least_connection_member': 'weighted-least-connections-member',
            'weighted_least_connection_node_address': 'weighted-least-connections-node',
            'ratio_least_connection_member': 'ratio-least-connections-member',
            'ratio_least_connection_node_address': 'ratio-least-connections-node'
        }
        lb_method = self._values['lb_method']
        if lb_method is None:
            return None

        spec = ArgumentSpec()
        if lb_method in spec.lb_choice_removed:
            raise F5ModuleError(
                "The provided lb_method is not supported"
            )
        if lb_method in spec.lb_choice_deprecated:
            self._values['__warnings'].append(
                dict(
                    msg="The provided lb_method '{0}' is deprecated".format(lb_method),
                    version='2.4'
                )
            )
            lb_method = lb_map.get(lb_method, lb_method.replace('_', '-'))
        if lb_method not in spec.lb_choice:
            raise F5ModuleError('Provided lb_method is unknown')
        return lb_method

    def _fqdn_name(self, value):
        if value is not None and not value.startswith('/'):
            return '/{0}/{1}'.format(self.partition, value)
        return value

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
        monitors = [self._fqdn_name(x) for x in self.monitors_list]
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
        if self.kind == 'tm:ltm:pool:poolstate':
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

    @property
    def host(self):
        value = self._values['host']
        if value is None:
            return None
        msg = "'%s' is not a valid IP address" % value
        try:
            IPAddress(value)
        except AddrFormatError:
            raise F5ModuleError(msg)
        return value

    @host.setter
    def host(self, value):
        self._values['host'] = value

    @property
    def port(self):
        value = self._values['port']
        if value is None:
            return None
        msg = "The provided port '%s' must be between 0 and 65535" % value
        if value < 0 or value > 65535:
            raise F5ModuleError(msg)
        return value

    @port.setter
    def port(self, value):
        self._values['port'] = value

    @property
    def member_name(self):
        if self.host is None or self.port is None:
            return None
        mname = str(self.host) + ':' + str(self.port)
        return mname

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(
                    self, self.api_map[api_attribute]
                )
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class Changes(Parameters):
    pass


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


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Changes()

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        return result

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Parameters(changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                changed[k] = change
        if changed:
            self.changes = Parameters(changed)
            return True
        return False

    def _member_does_not_exist(self, members):
        name = self.want.member_name
        # Return False if name is None, so that we don't attempt to create it
        if name is None:
            return False
        for member in members:
            if member.name == name:
                host, port = name.split(':')
                self.have.host = host
                self.have.port = int(port)
                return False
        return True

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update(self):
        self.have, members, poolres = self.read_current_from_device()
        if not self.client.check_mode:
            if self._member_does_not_exist(members):
                self.create_member_on_device(poolres)
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the Pool")
        return True

    def create(self):
        if self.want.monitor_type is not None:
            if not self.want.monitors_list:
                raise F5ModuleError(
                    "The 'monitors' parameter cannot be empty when 'monitor_type' parameter is specified"
                )
        else:
            if self.want.monitor_type is None:
                self.want.update(dict(monitor_type='and_list'))

        if self.want.monitor_type == 'm_of_n' and self.want.quorum is None:
            raise F5ModuleError(
                "Quorum value must be specified with monitor_type 'm_of_n'."
            )
        elif self.want.monitor_type == 'single' and len(self.want.monitors_list) > 1:
            raise F5ModuleError(
                "When using a 'monitor_type' of 'single', only one monitor may be provided"
            )

        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        if self.want.member_name:
            self.have, members, poolres = self.read_current_from_device()
            if self._member_does_not_exist(members):
                self.create_member_on_device(poolres)
        return True

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.ltm.pools.pool.create(
            partition=self.want.partition, **params
        )

    def create_member_on_device(self, poolres):
        poolres.members_s.members.create(
            name=self.want.member_name,
            partition=self.want.partition
        )

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def exists(self):
        return self.client.api.tm.ltm.pools.pool.exists(
            name=self.want.name,
            partition=self.want.partition
        )

    def remove_from_device(self):
        result = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if self.want.member_name and self.want.port and self.want.pool:
            member = result.members_s.members.load(
                name=self.want.member_name,
                partition=self.want.partition
            )
            if member:
                member.delete()
                self.delete_node_on_device()
        else:
            result.delete()

    def read_current_from_device(self):
        tmp_res = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        members = tmp_res.members_s.get_collection()

        result = tmp_res.attrs
        return Parameters(result), members, tmp_res

    def delete_node_on_device(self):
        resource = self.client.api.tm.ltm.nodes.node.load(
            name=self.want.host,
            partition=self.want.partition
        )
        try:
            resource.delete()
        except iControlUnexpectedHTTPError as e:
            # If we cannot remove it, it is in use, it is up to user to delete
            # it later.
            if "is referenced by a member of pool" in str(e):
                return
            else:
                raise


class ArgumentSpec(object):
    def __init__(self):
        self.lb_choice_deprecated = [
            'round_robin',
            'ratio_member',
            'least_connection_member',
            'observed_member',
            'predictive_member',
            'ratio_node_address',
            'least_connection_node_address',
            'fastest_node_address',
            'observed_node_address',
            'predictive_node_address',
            'dynamic_ratio',
            'fastest_app_response',
            'least_sessions',
            'dynamic_ratio_member',
            'ratio_session',
            'weighted_least_connection_member',
            'ratio_least_connection_member',
            'weighted_least_connection_node_address',
            'ratio_least_connection_node_address'
        ]
        self.lb_choice_removed = [
            'l3_addr'
        ]
        self.lb_choice = [
            'dynamic-ratio-member',
            'dynamic-ratio-node',
            'fastest-app-response',
            'fastest-node',
            'least-connections-member',
            'least-connections-node',
            'least-sessions',
            'observed-member',
            'observed-node',
            'predictive-member',
            'predictive-node',
            'ratio-least-connections-member',
            'ratio-least-connections-node',
            'ratio-member',
            'ratio-node',
            'ratio-session',
            'round-robin',
            'weighted-least-connections-member',
            'weighted-least-connections-node'
        ]
        lb_choices = self.lb_choice_removed + self.lb_choice + self.lb_choice_deprecated
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(
                required=True,
                aliases=['pool']
            ),
            lb_method=dict(
                choices=lb_choices
            ),
            monitor_type=dict(
                choices=[
                    'and_list', 'm_of_n', 'single'
                ]
            ),
            quorum=dict(
                type='int'
            ),
            monitors=dict(
                type='list'
            ),
            slow_ramp_time=dict(
                type='int'
            ),
            reselect_tries=dict(
                type='int'
            ),
            service_down_action=dict(
                choices=[
                    'none', 'reset',
                    'drop', 'reselect'
                ]
            ),
            description=dict(),
            host=dict(
                aliases=['address'],
                removed_in_version='2.4'
            ),
            port=dict(
                type='int',
                removed_in_version='2.4'
            )
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    if not HAS_NETADDR:
        raise F5ModuleError("The python netaddr module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        cleanup_tokens(client)
        client.module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
