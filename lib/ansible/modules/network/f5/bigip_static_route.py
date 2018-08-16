#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
module: bigip_static_route
short_description: Manipulate static routes on a BIG-IP
description:
  - Manipulate static routes on a BIG-IP.
version_added: 2.5
options:
  name:
    description:
      - Name of the static route.
    required: True
  description:
    description:
      - Descriptive text that identifies the route.
  destination:
    description:
      - Specifies an IP address for the static entry in the routing table.
        When creating a new static route, this value is required.
      - This value cannot be changed once it is set.
  netmask:
    description:
      - The netmask for the static route. When creating a new static route, this value
        is required.
      - This value can be in either IP or CIDR format.
      - This value cannot be changed once it is set.
  gateway_address:
    description:
      - Specifies the router for the system to use when forwarding packets
        to the destination host or network. Also known as the next-hop router
        address. This can be either an IPv4 or IPv6 address. When it is an
        IPv6 address that starts with C(FE80:), the address will be treated
        as a link-local address. This requires that the C(vlan) parameter
        also be supplied.
  vlan:
    description:
      - Specifies the VLAN or Tunnel through which the system forwards packets
        to the destination. When C(gateway_address) is a link-local IPv6
        address, this value is required
  pool:
    description:
      - Specifies the pool through which the system forwards packets to the
        destination.
  reject:
    description:
      - Specifies that the system drops packets sent to the destination.
    type: bool
  mtu:
    description:
      - Specifies a specific maximum transmission unit (MTU).
  route_domain:
    description:
      - The route domain id of the system. When creating a new static route, if
        this value is not specified, a default value of C(0) will be used.
      - This value cannot be changed once it is set.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.6
  state:
    description:
      - When C(present), ensures that the static route exists.
      - When C(absent), ensures that the static does not exist.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the netaddr Python package on the host. This is as easy as pip
    install netaddr.
extends_documentation_fragment: f5
requirements:
  - netaddr
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create static route with gateway address
  bigip_static_route:
    destination: 10.10.10.10
    netmask: 255.255.255.255
    gateway_address: 10.2.2.3
    name: test-route
    password: secret
    server: lb.mydomain.come
    user: admin
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
vlan:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
gateway_address:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
destination:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
route_domain:
  description: Route domain of the static route.
  returned: changed
  type: int
  sample: 1
netmask:
  description: Netmask of the destination.
  returned: changed
  type: string
  sample: 255.255.255.255
pool:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
partition:
  description: The partition that the static route was created on.
  returned: changed
  type: string
  sample: Common
description:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
reject:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
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
        'tmInterface': 'vlan',
        'gw': 'gateway_address',
        'network': 'destination',
        'blackhole': 'reject'
    }

    updatables = [
        'description', 'gateway_address', 'vlan',
        'pool', 'mtu', 'reject', 'destination', 'route_domain',
        'netmask'
    ]

    returnables = [
        'vlan', 'gateway_address', 'destination', 'pool', 'description',
        'reject', 'mtu', 'netmask', 'route_domain'
    ]

    api_attributes = [
        'tmInterface', 'gw', 'network', 'blackhole', 'description', 'pool', 'mtu'
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    @property
    def reject(self):
        if self._values['reject'] in BOOLEANS_TRUE:
            return True


class ModuleParameters(Parameters):
    @property
    def vlan(self):
        if self._values['vlan'] is None:
            return None
        return fq_name(self.partition, self._values['vlan'])

    @property
    def gateway_address(self):
        if self._values['gateway_address'] is None:
            return None
        try:
            ip = netaddr.IPNetwork(self._values['gateway_address'])
            return str(ip.ip)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided gateway_address is not an IP address"
            )

    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        result = int(self._values['route_domain'])
        return result

    @property
    def destination(self):
        if self._values['destination'] is None:
            return None
        if self._values['destination'] == 'default':
            self._values['destination'] = '0.0.0.0/0'
        if self._values['destination'] == 'default-inet6':
            self._values['destination'] = '::/::'
        try:
            ip = netaddr.IPNetwork(self.destination_ip)
            if self.route_domain:
                return '{0}%{2}/{1}'.format(ip.ip, ip.prefixlen, self.route_domain)
            else:
                return '{0}/{1}'.format(ip.ip, ip.prefixlen)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided destination is not an IP address"
            )

    @property
    def destination_ip(self):
        if self._values['destination']:
            ip = netaddr.IPNetwork('{0}/{1}'.format(self._values['destination'], self.netmask))
            return '{0}/{1}'.format(ip.ip, ip.prefixlen)

    @property
    def netmask(self):
        if self._values['netmask'] is None:
            return None
        # Check if numeric
        if isinstance(self._values['netmask'], int):
            result = int(self._values['netmask'])
            if 0 < result < 256:
                return result
            raise F5ModuleError(
                'The provided netmask {0} is neither in IP or CIDR format'.format(result)
            )
        else:
            try:
                # IPv4 netmask
                address = '0.0.0.0/' + self._values['netmask']
                ip = netaddr.IPNetwork(address)
            except netaddr.AddrFormatError as ex:
                try:
                    # IPv6 netmask
                    address = '::/' + self._values['netmask']
                    ip = netaddr.IPNetwork(address)
                except netaddr.AddrFormatError as ex:
                    raise F5ModuleError(
                        'The provided netmask {0} is neither in IP or CIDR format'.format(self._values['netmask'])
                    )
            result = int(ip.prefixlen)
        return result


class ApiParameters(Parameters):
    @property
    def route_domain(self):
        if self._values['destination'] is None:
            return None
        pattern = r'([0-9:]%(?P<rd>[0-9]+))'
        matches = re.search(pattern, self._values['destination'])
        if matches:
            return int(matches.group('rd'))
        return 0

    @property
    def destination_ip(self):
        if self._values['destination'] is None:
            return None
        if self._values['destination'] == 'default':
            self._values['destination'] = '0.0.0.0/0'
        if self._values['destination'] == 'default-inet6':
            self._values['destination'] = '::/::'
        try:
            pattern = r'(?P<rd>%[0-9]+)'
            addr = re.sub(pattern, '', self._values['destination'])
            ip = netaddr.IPNetwork(addr)
            return '{0}/{1}'.format(ip.ip, ip.prefixlen)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided destination is not an IP address"
            )

    @property
    def netmask(self):
        ip = netaddr.IPNetwork(self.destination_ip)
        return int(ip.prefixlen)


class Changes(Parameters):
    pass


class UsableChanges(Parameters):
    pass


class ReportableChanges(Parameters):
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
    def destination(self):
        if self.want.destination_ip is None:
            return None
        if self.want.destination_ip != self.have.destination_ip:
            raise F5ModuleError(
                "The destination cannot be changed. Delete and recreate "
                "the static route if you need to do this."
            )

    @property
    def route_domain(self):
        if self.want.route_domain is None:
            return None
        if self.want.route_domain is None and self.have.route_domain == 0:
            return None
        if self.want.route_domain != self.have.route_domain:
            raise F5ModuleError("You cannot change the route domain.")

    @property
    def netmask(self):
        if self.want.netmask is None:
            return None
        # It's easiest to just check the netmask by comparing dest IPs.
        if self.want.destination_ip != self.have.destination_ip:
            raise F5ModuleError(
                "The netmask cannot be changed. Delete and recreate "
                "the static route if you need to do this."
            )


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
                if k in ['netmask', 'route_domain']:
                    changed['address'] = change
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

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

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

    def exists(self):
        collection = self.client.api.tm.net.routes.get_collection()
        for resource in collection:
            if resource.name == self.want.name:
                if resource.partition == self.want.partition:
                    return True
        return False

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def create(self):
        required_resources = ['pool', 'vlan', 'reject', 'gateway_address']
        self._set_changed_options()
        if self.want.destination is None:
            raise F5ModuleError(
                'destination must be specified when creating a static route'
            )
        if self.want.netmask is None:
            raise F5ModuleError(
                'netmask must be specified when creating a static route'
            )
        if all(getattr(self.want, v) is None for v in required_resources):
            raise F5ModuleError(
                "You must specify at least one of " + ', '.join(required_resources)
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
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
        return True

    def update_on_device(self):
        params = self.want.api_params()

        # The 'network' attribute is not updatable
        params.pop('network', None)
        result = self.client.api.tm.net.routes.route.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result.modify(**params)

    def read_current_from_device(self):
        resource = self.client.api.tm.net.routes.route.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.net.routes.route.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the static route")
        return True

    def remove_from_device(self):
        result = self.client.api.tm.net.routes.route.load(
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
            description=dict(),
            destination=dict(),
            netmask=dict(),
            gateway_address=dict(),
            vlan=dict(),
            pool=dict(),
            mtu=dict(),
            reject=dict(
                type='bool'
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            route_domain=dict(type='int')
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.mutually_exclusive = [
            ['gateway_address', 'vlan', 'pool', 'reject']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
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
