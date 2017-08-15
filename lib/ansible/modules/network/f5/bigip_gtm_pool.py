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
module: bigip_gtm_pool
short_description: Manages F5 BIG-IP GTM pools.
description:
    - Manages F5 BIG-IP GTM pools.
version_added: "2.4"
options:
  state:
    description:
        - Pool member state. When C(present), ensures that the pool is
          created and enabled. When C(absent), ensures that the pool is
          removed from the system. When C(enabled) or C(disabled), ensures
          that the pool is enabled or disabled (respectively) on the remote
          device.
    required: True
    choices:
      - present
      - absent
      - enabled
      - disabled
  preferred_lb_method:
    description:
      - The load balancing mode that the system tries first.
    choices:
      - round-robin
      - return-to-dns
      - ratio
      - topology
      - static-persistence
      - global-availability
      - virtual-server-capacity
      - least-connections
      - lowest-round-trip-time
      - fewest-hops
      - packet-rate
      - cpu
      - completion-rate
      - quality-of-service
      - kilobytes-per-second
      - drop-packet
      - fallback-ip
      - virtual-server-score
  alternate_lb_method:
    description:
      - The load balancing mode that the system tries if the
        C(preferred_lb_method) is unsuccessful in picking a pool.
    choices:
      - round-robin
      - return-to-dns
      - none
      - ratio
      - topology
      - static-persistence
      - global-availability
      - virtual-server-capacity
      - packet-rate
      - drop-packet
      - fallback-ip
      - virtual-server-score
  fallback_lb_method:
    description:
      - The load balancing mode that the system tries if both the
        C(preferred_lb_method) and C(alternate_lb_method)s are unsuccessful
        in picking a pool.
    choices:
      - round-robin
      - return-to-dns
      - ratio
      - topology
      - static-persistence
      - global-availability
      - virtual-server-capacity
      - least-connections
      - lowest-round-trip-time
      - fewest-hops
      - packet-rate
      - cpu
      - completion-rate
      - quality-of-service
      - kilobytes-per-second
      - drop-packet
      - fallback-ip
      - virtual-server-score
  fallback_ip:
    description:
      - Specifies the IPv4, or IPv6 address of the server to which the system
        directs requests when it cannot use one of its pools to do so.
        Note that the system uses the fallback IP only if you select the
        C(fallback_ip) load balancing method.
  type:
    description:
      - The type of GTM pool that you want to create. On BIG-IP releases
        prior to version 12, this parameter is not required. On later versions
        of BIG-IP, this is a required parameter.
    choices:
      - a
      - aaaa
      - cname
      - mx
      - naptr
      - srv
  name:
    description:
      - Name of the GTM pool.
    required: True
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as
    pip install f5-sdk.
  - Requires the netaddr Python package on the host. This is as easy as
    pip install netaddr.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
  - netaddr
author:
  - Tim Rupp (@caphrim007)
'''

RETURN = '''
preferred_lb_method:
    description: New preferred load balancing method for the pool.
    returned: changed
    type: string
    sample: "topology"
alternate_lb_method:
    description: New alternate load balancing method for the pool.
    returned: changed
    type: string
    sample: "drop-packet"
fallback_lb_method:
    description: New fallback load balancing method for the pool.
    returned: changed
    type: string
    sample: "fewest-hops"
fallback_ip:
    description: New fallback IP used when load balacing using the C(fallback_ip) method.
    returned: changed
    type: string
    sample: "10.10.10.10"
'''

EXAMPLES = '''
- name: Create a GTM pool
  bigip_gtm_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      name: "my_pool"
  delegate_to: localhost

- name: Disable pool
  bigip_gtm_pool:
      server: "lb.mydomain.com"
      user: "admin"
      password: "secret"
      state: "disabled"
      name: "my_pool"
  delegate_to: localhost
'''


from distutils.version import LooseVersion
from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)

try:
    from netaddr import IPAddress, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False

import copy


class Parameters(AnsibleF5Parameters):
    api_map = {
        'loadBalancingMode': 'preferred_lb_method',
        'alternateMode': 'alternate_lb_method',
        'fallbackMode': 'fallback_lb_method',
        'verifyMemberAvailability': 'verify_member_availability',
        'fallbackIpv4': 'fallback_ip',
        'fallbackIpv6': 'fallback_ip',
        'fallbackIp': 'fallback_ip'
    }
    updatables = [
        'preferred_lb_method', 'alternate_lb_method', 'fallback_lb_method',
        'fallback_ip'
    ]
    returnables = [
        'preferred_lb_method', 'alternate_lb_method', 'fallback_lb_method',
        'fallback_ip'
    ]
    api_attributes = [
        'loadBalancingMode', 'alternateMode', 'fallbackMode', 'verifyMemberAvailability',
        'fallbackIpv4', 'fallbackIpv6', 'fallbackIp'
    ]

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
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result

    @property
    def collection(self):
        type_map = dict(
            a='a_s',
            aaaa='aaaas',
            cname='cnames',
            mx='mxs',
            naptr='naptrs',
            srv='srvs'
        )
        if self._values['type'] is None:
            return None
        wideip_type = self._values['type']
        return type_map[wideip_type]

    @property
    def type(self):
        if self._values['type'] is None:
            return None
        return str(self._values['type'])

    @property
    def verify_member_availability(self):
        if self._values['verify_member_availability'] is None:
            return None
        elif self._values['verify_member_availability']:
            return 'enabled'
        else:
            return 'disabled'

    @property
    def fallback_ip(self):
        if self._values['fallback_ip'] is None:
            return None
        if self._values['fallback_ip'] == 'any':
            return 'any'
        try:
            address = IPAddress(self._values['fallback_ip'])
            if address.version == 4:
                return str(address.ip)
            elif address.version == 6:
                return str(address.ip)
            return None
        except AddrFormatError:
            raise F5ModuleError(
                'The provided fallback address is not a valid IPv4 address'
            )

    @property
    def state(self):
        if self._values['state'] == 'enabled':
            return 'present'
        return self._values['state']

    @property
    def enabled(self):
        if self._values['state'] == 'disabled':
            return False
        elif self._values['state'] in ['present', 'enabled']:
            return True
        elif self._values['enabled'] is True:
            return True
        else:
            return None

    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True
        elif self._values['state'] in ['present', 'enabled']:
            return False
        elif self._values['disabled'] is True:
            return True
        else:
            return None


class ModuleManager(object):
    def __init__(self, client):
        self.client = client

    def exec_module(self):
        if not self.gtm_provisioned():
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
        if self.version_is_less_than_12():
            manager = self.get_manager('untyped')
        else:
            manager = self.get_manager('typed')
        return manager.exec_module()

    def get_manager(self, type):
        if type == 'typed':
            return TypedManager(self.client)
        elif type == 'untyped':
            return UntypedManager(self.client)

    def version_is_less_than_12(self):
        version = self.client.api.tmos_version
        if LooseVersion(version) < LooseVersion('12.0.0'):
            return True
        else:
            return False

    def gtm_provisioned(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name='provisioned.cpu.gtm'
        )
        if int(resource.value) == 0:
            return False
        return True


class BaseManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

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

        if self.want.state == 'disabled' and self.have.enabled:
            changed['state'] = self.want.state
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            changed['state'] = self.want.state

        if changed:
            self.changes = Parameters(changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ["present", "disabled"]:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
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

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the GTM pool")

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the GTM pool")
        return True


class TypedManager(BaseManager):
    def __init__(self, client):
        super(TypedManager, self).__init__(client)
        if self.want.type is None:
            raise F5ModuleError(
                "The 'type' option is required for BIG-IP instances "
                "greater than or equal to 12.x"
            )

    def present(self):
        types = [
            'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
        ]
        if self.want.type is None:
            raise F5ModuleError(
                "A pool 'type' must be specified"
            )
        elif self.want.type not in types:
            raise F5ModuleError(
                "The specified pool type is invalid"
            )

        return super(TypedManager, self).present()

    def exists(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.want.api_params()
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def read_current_from_device(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        result = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = result.attrs
        return Parameters(result)

    def create_on_device(self):
        params = self.want.api_params()
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        pools = self.client.api.tm.gtm.pools
        collection = getattr(pools, self.want.collection)
        resource = getattr(collection, self.want.type)
        resource = resource.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()


class UntypedManager(BaseManager):
    def exists(self):
        result = self.client.api.tm.gtm.pools.pool.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.gtm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def read_current_from_device(self):
        resource = self.client.api.tm.gtm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(result)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.gtm.pools.pool.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove_from_device(self):
        resource = self.client.api.tm.gtm.pools.pool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.states = ['absent', 'present', 'enabled', 'disabled']
        self.preferred_lb_methods = [
            'round-robin', 'return-to-dns', 'ratio', 'topology',
            'static-persistence', 'global-availability',
            'virtual-server-capacity', 'least-connections',
            'lowest-round-trip-time', 'fewest-hops', 'packet-rate', 'cpu',
            'completion-rate', 'quality-of-service', 'kilobytes-per-second',
            'drop-packet', 'fallback-ip', 'virtual-server-score'
        ]
        self.alternate_lb_methods = [
            'round-robin', 'return-to-dns', 'none', 'ratio', 'topology',
            'static-persistence', 'global-availability',
            'virtual-server-capacity', 'packet-rate', 'drop-packet',
            'fallback-ip', 'virtual-server-score'
        ]
        self.fallback_lb_methods = copy.copy(self.preferred_lb_methods)
        self.fallback_lb_methods.append('none')
        self.types = [
            'a', 'aaaa', 'cname', 'mx', 'naptr', 'srv'
        ]
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(required=True),
            state=dict(
                default='present',
                choices=self.states,
            ),
            preferred_lb_method=dict(
                choices=self.preferred_lb_methods,
            ),
            fallback_lb_method=dict(
                choices=self.fallback_lb_methods,
            ),
            alternate_lb_method=dict(
                choices=self.alternate_lb_methods,
            ),
            fallback_ip=dict(),
            type=dict(
                choices=self.types
            )
        )
        self.required_if = [
            ['preferred_lb_method', 'fallback-ip', ['fallback_ip']],
            ['fallback_lb_method', 'fallback-ip', ['fallback_ip']],
            ['alternate_lb_method', 'fallback-ip', ['fallback_ip']]
        ]
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    if not HAS_NETADDR:
        raise F5ModuleError("The python netaddr module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
