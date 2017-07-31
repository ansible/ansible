#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bigip_pool
short_description: Manages F5 BIG-IP LTM pools.
description:
  - Manages F5 BIG-IP LTM pools via iControl REST API.
version_added: 1.2
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
notes:
  - Requires BIG-IP software version >= 11.
  - F5 developed module 'F5-SDK' required (https://github.com/F5Networks/f5-common-python).
  - Best run as a local_action in your playbook.
requirements:
  - f5-sdk
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
      - Monitor rule type when C(monitors) > 1.
    version_added: "1.3"
    choices: ['and_list', 'm_of_n']
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
    aliases:
      - address
  port:
    description:
      - Pool member port.
extends_documentation_fragment: f5
'''

EXAMPLES = '''
- name: Create pool
  bigip_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      name: "my-pool"
      partition: "Common"
      lb_method: "least_connection_member"
      slow_ramp_time: 120
  delegate_to: localhost

- name: Modify load balancer method
  bigip_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      name: "my-pool"
      partition: "Common"
      lb_method: "round_robin"
  delegate_to: localhost

- name: Add pool member
  bigip_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "present"
      name: "my-pool"
      partition: "Common"
      host: "{{ ansible_default_ipv4['address'] }}"
      port: 80
  delegate_to: localhost

- name: Remove pool member from pool
  bigip_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "absent"
      name: "my-pool"
      partition: "Common"
      host: "{{ ansible_default_ipv4['address'] }}"
      port: 80
  delegate_to: localhost

- name: Delete pool
  bigip_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "absent"
      name: "my-pool"
      partition: "Common"
  delegate_to: localhost
'''

RETURN = '''
monitor_type:
    description: The contact that was set on the datacenter.
    returned: changed
    type: string
    sample: "admin@root.local"
quorum:
    description: The quorum that was set on the pool
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
    sample: "reset"
description:
    description: Description set on the pool.
    returned: changed
    type: string
    sample: "Pool of web servers"
lb_method:
    description: The LB method set for the pool.
    returned: changed
    type: string
    sample: "round-robin"
host:
    description: IP of pool member included in pool.
    returned: changed
    type: string
    sample: "10.10.10.10"
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
    description: The new value that is set for the number of tries to contact member
    returned: changed
    type: int
    sample: 10
'''

import re
import os
from netaddr import IPAddress, AddrFormatError
from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)


class Parameters(AnsibleF5Parameters):
    api_map = {
        'loadBalancingMode': 'lb_method',
        'slowRampTime': 'slow_ramp_time',
        'reselectTries': 'reselect_tries',
        'serviceDownAction': 'service_down_action'
    }

    updatables = [
        'monitor_type', 'quorum', 'monitors', 'service_down_action',
        'description', 'lb_method', 'slow_ramp_time', 'reselect_tries',
        'host', 'port'
    ]

    returnables = [
        'monitor_type', 'quorum', 'monitors', 'service_down_action',
        'description', 'lb_method', 'host', 'port', 'slow_ramp_time',
        'reselect_tries', 'monitor', 'member_name', 'name', 'partition'
    ]

    api_attributes = [
        'description', 'name', 'loadBalancingMode', 'monitor', 'slowRampTime',
        'reselectTries', 'serviceDownAction'
    ]

    def __init__(self, params=None):
        super(Parameters, self).__init__(params)
        self._values['__warnings'] = []

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
        try:
            assert lb_method in spec.lb_choice
        except AssertionError:
            raise F5ModuleError('Provided lb_method is unknown')
        return lb_method

    @property
    def monitors(self):
        monitors = list()
        monitor_list = self._values['monitors']
        monitor_type = self._values['monitor_type']
        error1 = "The 'monitor_type' parameter cannot be empty when " \
                 "'monitors' parameter is specified."
        error2 = "The 'monitor' parameter cannot be empty when " \
                 "'monitor_type' parameter is specified"
        if monitor_list is not None and monitor_type is None:
            raise F5ModuleError(error1)
        elif monitor_list is None and monitor_type is not None:
            raise F5ModuleError(error2)
        elif monitor_list is None:
            return None

        for m in monitor_list:
            if re.match(r'\/\w+\/\w+', m):
                m = '/{0}/{1}'.format(self.partition, os.path.basename(m))
            elif re.match(r'\w+', m):
                m = '/{0}/{1}'.format(self.partition, m)
            else:
                raise F5ModuleError(
                    "Unknown monitor format '{0}'".format(m)
                )
            monitors.append(m)

        return monitors

    @property
    def quorum(self):
        value = self._values['quorum']
        error = "Quorum value must be specified with monitor_type 'm_of_n'."
        if self._values['monitor_type'] == 'm_of_n' and value is None:
            raise F5ModuleError(error)
        return value

    @property
    def monitor(self):
        monitors = self.monitors
        monitor_type = self._values['monitor_type']
        quorum = self.quorum

        if monitors is None:
            return None

        if monitor_type == 'and_list':
            and_list = list()
            for m in monitors:
                if monitors.index(m) == 0:
                    and_list.append(m)
                else:
                    and_list.append('and')
                    and_list.append(m)
            result = ' '.join(and_list)
        else:
            min_list = list()
            prefix = 'min {0} of {{'.format(str(quorum))
            min_list.append(prefix)
            for m in monitors:
                min_list.append(m)
            min_list.append('}')
            result = ' '.join(min_list)

        return result

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


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

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
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
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
                    'and_list', 'm_of_n'
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


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
