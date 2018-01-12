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
module: bigip_gtm_pool
short_description: Manages F5 BIG-IP GTM pools
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
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
notes:
  - Requires the netaddr Python package on the host. This is as easy as
    pip install netaddr.
extends_documentation_fragment: f5
requirements:
  - netaddr
author:
  - Tim Rupp (@caphrim007)
'''

RETURN = r'''
preferred_lb_method:
  description: New preferred load balancing method for the pool.
  returned: changed
  type: string
  sample: topology
alternate_lb_method:
  description: New alternate load balancing method for the pool.
  returned: changed
  type: string
  sample: drop-packet
fallback_lb_method:
  description: New fallback load balancing method for the pool.
  returned: changed
  type: string
  sample: fewest-hops
fallback_ip:
  description: New fallback IP used when load balacing using the C(fallback_ip) method.
  returned: changed
  type: string
  sample: 10.10.10.10
'''

EXAMPLES = r'''
- name: Create a GTM pool
  bigip_gtm_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my_pool
  delegate_to: localhost

- name: Disable pool
  bigip_gtm_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    state: disabled
    name: my_pool
  delegate_to: localhost
'''

from distutils.version import LooseVersion
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

HAS_DEVEL_IMPORTS = False

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
        'fallback_ip', 'state'
    ]
    returnables = [
        'preferred_lb_method', 'alternate_lb_method', 'fallback_lb_method',
        'fallback_ip'
    ]
    api_attributes = [
        'loadBalancingMode', 'alternateMode', 'fallbackMode', 'verifyMemberAvailability',
        'fallbackIpv4', 'fallbackIpv6', 'fallbackIp', 'enabled', 'disabled'
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
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
        if self._values['fallback_ip'] == 'any6':
            return 'any6'
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
        if self._values['enabled'] is None:
            return None
        return True

    @property
    def disabled(self):
        if self._values['disabled'] is None:
            return None
        return True


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
    def state(self):
        if self.want.state == 'disabled' and self.have.enabled:
            return dict(
                disabled=True
            )
        elif self.want.state in ['present', 'enabled'] and self.have.disabled:
            return dict(
                enabled=True
            )


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs
        self.client = kwargs.get('client', None)

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
            return TypedManager(**self.kwargs)
        elif type == 'untyped':
            return UntypedManager(**self.kwargs)

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
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

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
            self.changes = Changes(params=changed)
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
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def create(self):
        if self.want.state == 'disabled':
            self.want.update({'disabled': True})
        elif self.want.state in ['present', 'enabled']:
            self.want.update({'enabled': True})
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the GTM pool")

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the GTM pool")
        return True


class TypedManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super(TypedManager, self).__init__(**kwargs)
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
        params = self.changes.api_params()
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
        return Parameters(params=result)

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
        params = self.changes.api_params()
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
        return Parameters(params=result)

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
        argument_spec = dict(
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
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['preferred_lb_method', 'fallback-ip', ['fallback_ip']],
            ['fallback_lb_method', 'fallback-ip', ['fallback_ip']],
            ['alternate_lb_method', 'fallback-ip', ['fallback_ip']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
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
