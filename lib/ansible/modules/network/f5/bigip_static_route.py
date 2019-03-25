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
module: bigip_static_route
short_description: Manipulate static routes on a BIG-IP
description:
  - Manipulate static routes on a BIG-IP.
version_added: 2.5
options:
  name:
    description:
      - Name of the static route.
    type: str
    required: True
  description:
    description:
      - Descriptive text that identifies the route.
    type: str
  destination:
    description:
      - Specifies an IP address for the static entry in the routing table.
        When creating a new static route, this value is required.
      - This value cannot be changed once it is set.
    type: str
  netmask:
    description:
      - The netmask for the static route. When creating a new static route, this value
        is required.
      - This value can be in either IP or CIDR format.
      - This value cannot be changed once it is set.
    type: str
  gateway_address:
    description:
      - Specifies the router for the system to use when forwarding packets
        to the destination host or network. Also known as the next-hop router
        address. This can be either an IPv4 or IPv6 address. When it is an
        IPv6 address that starts with C(FE80:), the address will be treated
        as a link-local address. This requires that the C(vlan) parameter
        also be supplied.
    type: str
  vlan:
    description:
      - Specifies the VLAN or Tunnel through which the system forwards packets
        to the destination. When C(gateway_address) is a link-local IPv6
        address, this value is required.
    type: str
  pool:
    description:
      - Specifies the pool through which the system forwards packets to the
        destination.
    type: str
  reject:
    description:
      - Specifies that the system drops packets sent to the destination.
    type: bool
  mtu:
    description:
      - Specifies a specific maximum transmission unit (MTU).
    type: str
  route_domain:
    description:
      - The route domain id of the system. When creating a new static route, if
        this value is not specified, a default value of C(0) will be used.
      - This value cannot be changed once it is set.
    type: int
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.6
  state:
    description:
      - When C(present), ensures that the static route exists.
      - When C(absent), ensures that the static does not exist.
    type: str
    choices:
      - present
      - absent
    default: present
extends_documentation_fragment: f5
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
    provider:
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
  type: str
  sample: true
gateway_address:
  description: Whether the banner is enabled or not.
  returned: changed
  type: str
  sample: true
destination:
  description: Whether the banner is enabled or not.
  returned: changed
  type: str
  sample: true
route_domain:
  description: Route domain of the static route.
  returned: changed
  type: int
  sample: 1
netmask:
  description: Netmask of the destination.
  returned: changed
  type: str
  sample: 255.255.255.255
pool:
  description: Whether the banner is enabled or not.
  returned: changed
  type: str
  sample: true
partition:
  description: The partition that the static route was created on.
  returned: changed
  type: str
  sample: Common
description:
  description: Whether the banner is enabled or not.
  returned: changed
  type: str
  sample: true
reject:
  description: Whether the banner is enabled or not.
  returned: changed
  type: str
  sample: true
'''

import re

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import ipv6_netmask_to_cidr
    from library.module_utils.compat.ipaddress import ip_address
    from library.module_utils.compat.ipaddress import ip_network
    from library.module_utils.compat.ipaddress import ip_interface
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import ipv6_netmask_to_cidr
    from ansible.module_utils.compat.ipaddress import ip_address
    from ansible.module_utils.compat.ipaddress import ip_network
    from ansible.module_utils.compat.ipaddress import ip_interface


class Parameters(AnsibleF5Parameters):
    api_map = {
        'tmInterface': 'vlan',
        'gw': 'gateway_address',
        'network': 'destination',
        'blackhole': 'reject'
    }

    updatables = [
        'description',
        'gateway_address',
        'vlan',
        'pool',
        'mtu',
        'reject',
        'destination',
        'route_domain',
        'netmask',
    ]

    returnables = [
        'vlan',
        'gateway_address',
        'destination',
        'pool',
        'description',
        'reject',
        'mtu',
        'netmask',
        'route_domain',
    ]

    api_attributes = [
        'tmInterface',
        'gw',
        'network',
        'blackhole',
        'description',
        'pool',
        'mtu',
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
            if '%' in self._values['gateway_address']:
                addr = self._values['gateway_address'].split('%')[0]
            else:
                addr = self._values['gateway_address']
            ip_interface(u'%s' % str(addr))
            return str(self._values['gateway_address'])
        except ValueError:
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
        if self._values['destination'].startswith('default'):
            self._values['destination'] = '0.0.0.0/0'
        if self._values['destination'].startswith('default-inet6'):
            self._values['destination'] = '::/0'
        try:
            ip = ip_network(u'%s' % str(self.destination_ip))
            if self.route_domain:
                return '{0}%{1}/{2}'.format(str(ip.network_address), self.route_domain, ip.prefixlen)
            else:
                return '{0}/{1}'.format(str(ip.network_address), ip.prefixlen)
        except ValueError:
            raise F5ModuleError(
                "The provided destination is not an IP address"
            )

    @property
    def destination_ip(self):
        if self._values['destination']:
            ip = ip_network(u'{0}/{1}'.format(self._values['destination'], self.netmask))
            return '{0}/{1}'.format(str(ip.network_address), ip.prefixlen)

    @property
    def netmask(self):
        if self._values['netmask'] is None:
            return None
        try:
            result = int(self._values['netmask'])

            # CIDRs between 0 and 128 are allowed
            if 0 <= result <= 128:
                return result
            else:
                raise F5ModuleError(
                    "The provided netmask must be between 0 and 32 for IPv4, or "
                    "0 and 128 for IPv6."
                )
        except ValueError:
            # not a number, but that's ok. Further processing necessary
            pass

        if not is_valid_ip(self._values['netmask']):
            raise F5ModuleError(
                'The provided netmask {0} is neither in IP or CIDR format'.format(result)
            )

        # Create a temporary address to check if the netmask IP is v4 or v6
        addr = ip_address(u'{0}'.format(str(self._values['netmask'])))
        if addr.version == 4:
            # Create a more real v4 address using a wildcard, so that we can determine
            # the CIDR value from it.
            ip = ip_network(u'0.0.0.0/%s' % str(self._values['netmask']))
            result = ip.prefixlen
        else:
            result = ipv6_netmask_to_cidr(self._values['netmask'])

        return result


class ApiParameters(Parameters):
    @property
    def route_domain(self):
        if self._values['destination'] is None:
            return None
        pattern = r'([0-9a-zA-Z\:\-\.]+%(?P<rd>[0-9]+))'
        matches = re.search(pattern, self._values['destination'])
        if matches:
            return int(matches.group('rd'))
        return 0

    @property
    def destination_ip(self):
        if self._values['destination'] is None:
            return None
        destination = self.destination_to_network()

        try:
            pattern = r'(?P<rd>%[0-9]+)'
            addr = re.sub(pattern, '', destination)
            ip = ip_network(u'%s' % str(addr))
            return '{0}/{1}'.format(str(ip.network_address), ip.prefixlen)
        except ValueError:
            raise F5ModuleError(
                "The provided destination is not an IP address."
            )

    @property
    def netmask(self):
        destination = self.destination_to_network()
        ip = ip_network(u'%s' % str(destination))
        return int(ip.prefixlen)

    def destination_to_network(self):
        destination = self._values['destination']
        if destination.startswith('default%'):
            destination = '0.0.0.0%{0}/0'.format(destination.split('%')[1])
        elif destination.startswith('default-inet6%'):
            destination = '::%{0}/0'.format(destination.split('%')[1])
        elif destination.startswith('default-inet6'):
            destination = '::/0'
        elif destination.startswith('default'):
            destination = '0.0.0.0/0'
        return destination


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

        if state == "present":
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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route/{2}".format(
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

        uri = "https://{0}:{1}/mgmt/tm/net/route/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/net/route/{2}".format(
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

    def create_on_device(self):
        params = self.want.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/net/route/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/net/route/{2}".format(
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
            ['gateway_address', 'pool', 'reject']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
