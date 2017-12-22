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
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  metdata:
    description:
      - Arbitrary key/value pairs that you can attach to a pool. This is useful in
        situations where you might want to annotate a pool to me managed by Ansible.
      - Key names will be stored as strings; this includes names that are numbers.
      - Values for all of the keys will be stored as strings; this includes values
        that are numbers.
      - Data will be persisted, not ephemeral.
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
    lb_method: least-connection-member
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
    lb_method: round-robin
  delegate_to: localhost

- name: Add pool member
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: present
    pool: my-pool
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
  bigip_pool_member:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: absent
    pool: my-pool
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

- name: Add metadata to pool
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
metadata:
  description: The new value of the pool.
  returned: changed
  type: dict
  sample: {'key1': 'foo', 'key2': 'bar'}
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
        'reselectTries', 'serviceDownAction', 'metadata'
    ]

    returnables = [
        'monitor_type', 'quorum', 'monitors', 'service_down_action',
        'description', 'lb_method', 'slow_ramp_time',
        'reselect_tries', 'monitor', 'name', 'partition', 'metadata'
    ]

    updatables = [
        'monitor_type', 'quorum', 'monitors', 'service_down_action',
        'description', 'lb_method', 'slow_ramp_time', 'reselect_tries',
        'metadata'
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
        lb_method = self._values['lb_method']
        if lb_method is None:
            return None

        spec = ArgumentSpec()
        if lb_method not in spec.lb_choice:
            raise F5ModuleError('Provided lb_method is unknown')
        return lb_method

    def _fqdn_name(self, value):
        if value is not None and not value.startswith('/'):
            return '/{0}/{1}'.format(self.partition, value)
        return value

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

    def _verify_quorum_type(self, quorum):
        try:
            if quorum is None:
                return None
            return int(quorum)
        except ValueError:
            raise F5ModuleError(
                "The specified 'quorum' must be an integer."
            )


class ApiParameters(Parameters):
    @property
    def quorum(self):
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+(?P<quorum>\d+)\s+of'
        matches = re.search(pattern, self._values['monitors'])
        if matches:
            quorum = matches.group('quorum')
        else:
            quorum = None
        result = self._verify_quorum_type(quorum)
        return result

    @property
    def monitor_type(self):
        if self._values['monitors'] is None:
            return None
        pattern = r'min\s+\d+\s+of'
        matches = re.search(pattern, self._values['monitors'])
        if matches:
            return 'm_of_n'
        else:
            return 'and_list'

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
    @property
    def monitors_list(self):
        if self._values['monitors'] is None:
            return []
        return self._values['monitors']

    @property
    def quorum(self):
        if self._values['quorum'] is None:
            return None
        result = self._verify_quorum_type(self._values['quorum'])
        return result

    @property
    def monitor_type(self):
        if self._values['monitor_type'] is None:
            return None
        return self._values['monitor_type']

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
    def to_return(self):
        result = {}
        for returnable in self.returnables:
            try:
                result[returnable] = getattr(self, returnable)
            except Exception:
                pass
            result = self._filter_params(result)
        return result

    @property
    def monitors(self):
        if self._values['monitors'] is None:
            return None
        return self._values['monitors']


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    @property
    def monitors(self):
        result = sorted(re.findall(r'/\w+/[^\s}]+', self._values['monitors']))
        return result

    @property
    def metadata(self):
        result = dict()
        for x in self._values['metadata']:
            result[x['name']] = x['value']
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
    def __init__(self, client):
        self.client = client
        self.want = ModuleParameters(params=self.client.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

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

        reportable = ReportableChanges(self.changes.to_return())
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

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(changed)

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
            self.changes = UsableChanges(changed)
            return True
        return False

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
        self.have = self.read_current_from_device()
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
        return True

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.ltm.pools.pool.create(
            partition=self.want.partition, **params
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
        result.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.ltm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition,
            requests_params=dict(
                params='expandSubcollections=true'
            )
        )
        return ApiParameters(resource.attrs)


class ArgumentSpec(object):
    def __init__(self):
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
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(
                required=True,
                aliases=['pool']
            ),
            lb_method=dict(
                choices=self.lb_choice
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
            metadata=dict(type='raw')
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
