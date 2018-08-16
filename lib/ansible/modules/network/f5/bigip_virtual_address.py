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
module: bigip_virtual_address
short_description: Manage LTM virtual addresses on a BIG-IP
description:
  - Manage LTM virtual addresses on a BIG-IP.
version_added: 2.4
options:
  name:
    description:
      - Name of the virtual address.
      - If this parameter is not provided, then the value of C(address) will
        be used.
    version_added: 2.6
  address:
    description:
      - Virtual address. This value cannot be modified after it is set.
      - If you never created a virtual address, but did create virtual servers, then
        a virtual address for each virtual server was created automatically. The name
        of this virtual address is its IP address value.
  netmask:
    description:
      - Netmask of the provided virtual address. This value cannot be
        modified after it is set.
    default: 255.255.255.255
  connection_limit:
    description:
      - Specifies the number of concurrent connections that the system
        allows on this virtual address.
  arp_state:
    description:
      - Specifies whether the system accepts ARP requests. When (disabled),
        specifies that the system does not accept ARP requests. Note that
        both ARP and ICMP Echo must be disabled in order for forwarding
        virtual servers using that virtual address to forward ICMP packets.
        If (enabled), then the packets are dropped.
    choices:
      - enabled
      - disabled
  auto_delete:
    description:
      - Specifies whether the system automatically deletes the virtual
        address with the deletion of the last associated virtual server.
        When C(disabled), specifies that the system leaves the virtual
        address even when all associated virtual servers have been deleted.
        When creating the virtual address, the default value is C(enabled).
    choices:
      - enabled
      - disabled
  icmp_echo:
    description:
      - Specifies how the systems sends responses to (ICMP) echo requests
        on a per-virtual address basis for enabling route advertisement.
        When C(enabled), the BIG-IP system intercepts ICMP echo request
        packets and responds to them directly. When C(disabled), the BIG-IP
        system passes ICMP echo requests through to the backend servers.
        When (selective), causes the BIG-IP system to internally enable or
        disable responses based on virtual server state; C(when_any_available),
        C(when_all_available, or C(always), regardless of the state of any
        virtual servers.
    choices:
      - enabled
      - disabled
      - selective
  state:
    description:
      - The virtual address state. If C(absent), an attempt to delete the
        virtual address will be made. This will only succeed if this
        virtual address is not in use by a virtual server. C(present) creates
        the virtual address and enables it. If C(enabled), enable the virtual
        address if it exists. If C(disabled), create the virtual address if
        needed, and set state to C(disabled).
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
  availability_calculation:
    description:
      - Specifies what routes of the virtual address the system advertises.
        When C(when_any_available), advertises the route when any virtual
        server is available. When C(when_all_available), advertises the
        route when all virtual servers are available. When (always), always
        advertises the route regardless of the virtual servers available.
    choices:
      - always
      - when_all_available
      - when_any_available
    aliases: ['advertise_route']
    version_added: 2.6
  use_route_advertisement:
    description:
      - Specifies whether the system uses route advertisement for this
        virtual address.
      - When disabled, the system does not advertise routes for this virtual address.
      - Deprecated. Use the C(route_advertisement) parameter instead.
    type: bool
  route_advertisement:
    description:
      - Specifies whether the system uses route advertisement for this
        virtual address.
      - When disabled, the system does not advertise routes for this virtual address.
      - The majority of these options are only supported on versions 13.0.0-HF1 or
        higher. On versions less than this, all choices expect C(disabled) will
        translate to C(enabled).
      - When C(always), the BIG-IP system will always advertise the route for the
        virtual address, regardless of availability status. This requires an C(enabled)
        virtual address.
      - When C(enabled), the BIG-IP system will advertise the route for the available
        virtual address, based on the calculation method in the availability calculation.
      - When C(disabled), the BIG-IP system will not advertise the route for the virtual
        address, regardless of the availability status.
      - When C(selective), you can also selectively enable ICMP echo responses, which
        causes the BIG-IP system to internally enable or disable responses based on
        virtual server state. Either C(any) virtual server, C(all) virtual servers, or
        C(always), regardless of the state of any virtual server.
      - When C(any), the BIG-IP system will advertise the route for the virtual address
        when any virtual server is available.
      - When C(all), the BIG-IP system will advertise the route for the virtual address
        when all virtual servers are available.
    choices:
      - disabled
      - enabled
      - always
      - selective
      - any
      - all
    version_added: 2.6
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  traffic_group:
    description:
      - The traffic group for the virtual address. When creating a new address,
        if this value is not specified, the default of C(/Common/traffic-group-1)
        will be used.
    version_added: 2.5
  route_domain:
    description:
      - The route domain of the C(address) that you want to use.
      - This value cannot be modified after it is set.
    version_added: 2.6
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
- name: Add virtual address
  bigip_virtual_address:
    server: lb.mydomain.net
    user: admin
    password: secret
    state: present
    partition: Common
    address: 10.10.10.10
  delegate_to: localhost

- name: Enable route advertisement on the virtual address
  bigip_virtual_address:
    server: lb.mydomain.net
    user: admin
    password: secret
    state: present
    address: 10.10.10.10
    use_route_advertisement: yes
  delegate_to: localhost
'''

RETURN = r'''
use_route_advertisement:
  description: The new setting for whether to use route advertising or not.
  returned: changed
  type: bool
  sample: true
auto_delete:
  description: New setting for auto deleting virtual address.
  returned: changed
  type: string
  sample: enabled
icmp_echo:
  description: New ICMP echo setting applied to virtual address.
  returned: changed
  type: string
  sample: disabled
connection_limit:
  description: The new connection limit of the virtual address.
  returned: changed
  type: int
  sample: 1000
netmask:
  description: The netmask of the virtual address.
  returned: created
  type: int
  sample: 2345
arp_state:
  description: The new way the virtual address handles ARP requests.
  returned: changed
  type: string
  sample: disabled
address:
  description: The address of the virtual address.
  returned: created
  type: int
  sample: 2345
state:
  description: The new state of the virtual address.
  returned: changed
  type: string
  sample: disabled
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE
from distutils.version import LooseVersion

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
        'routeAdvertisement': 'route_advertisement_type',
        'autoDelete': 'auto_delete',
        'icmpEcho': 'icmp_echo',
        'connectionLimit': 'connection_limit',
        'serverScope': 'availability_calculation',
        'mask': 'netmask',
        'arp': 'arp_state',
        'trafficGroup': 'traffic_group',
    }

    updatables = [
        'route_advertisement_type', 'auto_delete', 'icmp_echo', 'connection_limit',
        'arp_state', 'enabled', 'availability_calculation', 'traffic_group'
    ]

    returnables = [
        'route_advertisement_type', 'auto_delete', 'icmp_echo', 'connection_limit',
        'netmask', 'arp_state', 'address', 'state', 'traffic_group', 'route_domain'
    ]

    api_attributes = [
        'routeAdvertisement', 'autoDelete', 'icmpEcho', 'connectionLimit',
        'advertiseRoute', 'arp', 'mask', 'enabled', 'serverScope', 'trafficGroup'
    ]

    @property
    def availability_calculation(self):
        if self._values['availability_calculation'] is None:
            return None
        elif self._values['availability_calculation'] in ['any', 'when_any_available']:
            return 'any'
        elif self._values['availability_calculation'] in ['all', 'when_all_available']:
            return 'all'
        elif self._values['availability_calculation'] in ['none', 'always']:
            return 'none'

    @property
    def connection_limit(self):
        if self._values['connection_limit'] is None:
            return None
        return int(self._values['connection_limit'])

    @property
    def enabled(self):
        if self._values['state'] in ['enabled', 'present']:
            return 'yes'
        elif self._values['enabled'] in BOOLEANS_TRUE:
            return 'yes'
        elif self._values['state'] == 'disabled':
            return 'no'
        elif self._values['enabled'] in BOOLEANS_FALSE:
            return 'no'
        else:
            return None

    @property
    def netmask(self):
        if self._values['netmask'] is None:
            return None
        try:
            ip = netaddr.IPAddress(self._values['netmask'])
            return str(ip)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided 'netmask' is not a valid IP address"
            )

    @property
    def auto_delete(self):
        if self._values['auto_delete'] is None:
            return None
        elif self._values['auto_delete'] in BOOLEANS_TRUE:
            return True
        elif self._values['auto_delete'] == 'enabled':
            return True
        else:
            return False

    @property
    def state(self):
        if self.enabled == 'yes' and self._values['state'] != 'present':
            return 'enabled'
        elif self.enabled == 'no':
            return 'disabled'
        else:
            return self._values['state']

    @property
    def traffic_group(self):
        if self._values['traffic_group'] is None:
            return None
        else:
            result = fq_name(self.partition, self._values['traffic_group'])
        if result.startswith('/Common/'):
            return result
        else:
            raise F5ModuleError(
                "Traffic groups can only exist in /Common"
            )

    @property
    def route_advertisement_type(self):
        if self.use_route_advertisement:
            return self.use_route_advertisement
        elif self.route_advertisement:
            return self.route_advertisement
        else:
            return self._values['route_advertisement_type']

    @property
    def use_route_advertisement(self):
        if self._values['use_route_advertisement'] is None:
            return None
        if self._values['use_route_advertisement'] in BOOLEANS_TRUE:
            return 'enabled'
        elif self._values['use_route_advertisement'] == 'enabled':
            return 'enabled'
        else:
            return 'disabled'

    @property
    def route_advertisement(self):
        if self._values['route_advertisement'] is None:
            return None
        version = self.client.api.tmos_version
        if LooseVersion(version) <= LooseVersion('13.0.0'):
            if self._values['route_advertisement'] == 'disabled':
                return 'disabled'
            else:
                return 'enabled'
        else:
            return self._values['route_advertisement']

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def address(self):
        if self._values['address'] is None:
            return None
        try:
            ip = netaddr.IPAddress(self._values['address'])
            return str(ip)
        except netaddr.core.AddrFormatError:
            raise F5ModuleError(
                "The provided 'address' is not a valid IP address"
            )

    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        try:
            return int(self._values['route_domain'])
        except ValueError:
            try:
                rd = self.client.api.tm.net.route_domains.route_domain.load(
                    name=self._values['route_domain'],
                    partition=self.partition
                )
                return int(rd.id)
            except iControlUnexpectedHTTPError:
                raise F5ModuleError(
                    "The specified 'route_domain' was not found."
                )

    @property
    def full_address(self):
        if self.route_domain is not None:
            return '{0}%{1}'.format(self.address, self.route_domain)
        return self.address

    @property
    def name(self):
        if self._values['name'] is None:
            result = str(self.address)
            if self.route_domain:
                result = "{0}%{1}".format(result, self.route_domain)
        else:
            result = self._values['name']
        return result


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    @property
    def address(self):
        if self._values['address'] is None:
            return None
        if self._values['route_domain'] is None:
            return self._values['address']
        result = "{0}%{1}".format(self._values['address'], self._values['route_domain'])
        return result


class ReportableChanges(Changes):
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
    def traffic_group(self):
        if self.want.traffic_group != self.have.traffic_group:
            return self.want.traffic_group


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = ModuleParameters(client=self.client, params=self.module.params)
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

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['present', 'enabled', 'disabled']:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def absent(self):
        changed = False
        if self.exists():
            changed = self.remove()
        return changed

    def read_current_from_device(self):
        name = self.want.name
        name = name.replace('%', '%25')
        resource = self.client.api.tm.ltm.virtual_address_s.virtual_address.load(
            name=name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)

    def exists(self):
        # This addresses cases where the name includes a % sign. The URL in the REST
        # API escapes a % sign as %25. If you don't do this, you will get errors in
        # the exists() method.
        name = self.want.name
        name = name.replace('%', '%25')
        result = self.client.api.tm.ltm.virtual_address_s.virtual_address.exists(
            name=name,
            partition=self.want.partition
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if self.want.netmask is not None:
            if self.have.netmask != self.want.netmask:
                raise F5ModuleError(
                    "The netmask cannot be changed. Delete and recreate "
                    "the virtual address if you need to do this."
                )
        if self.want.address is not None:
            if self.have.address != self.want.full_address:
                raise F5ModuleError(
                    "The address cannot be changed. Delete and recreate "
                    "the virtual address if you need to do this."
                )
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        name = self.want.name
        name = name.replace('%', '%25')
        resource = self.client.api.tm.ltm.virtual_address_s.virtual_address.load(
            name=name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def create(self):
        self._set_changed_options()
        if self.want.traffic_group is None:
            self.want.update({'traffic_group': '/Common/traffic-group-1'})
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the virtual address")

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.ltm.virtual_address_s.virtual_address.create(
            name=self.want.name,
            partition=self.want.partition,
            address=self.changes.address,
            **params
        )

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the virtual address")
        return True

    def remove_from_device(self):
        name = self.want.name
        name = name.replace('%', '%25')
        resource = self.client.api.tm.ltm.virtual_address_s.virtual_address.load(
            name=name,
            partition=self.want.partition
        )
        resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            state=dict(
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
            ),
            name=dict(),
            address=dict(),
            netmask=dict(
                type='str',
                default='255.255.255.255',
            ),
            connection_limit=dict(
                type='int'
            ),
            arp_state=dict(
                choices=['enabled', 'disabled'],
            ),
            auto_delete=dict(
                choices=['enabled', 'disabled'],
            ),
            icmp_echo=dict(
                choices=['enabled', 'disabled', 'selective'],
            ),
            availability_calculation=dict(
                choices=['always', 'when_all_available', 'when_any_available'],
                aliases=['advertise_route']
            ),
            use_route_advertisement=dict(
                type='bool',
                removed_in_version=2.9,
            ),
            route_advertisement=dict(
                choices=[
                    'disabled',
                    'enabled',
                    'always',
                    'selective',
                    'any',
                    'all',
                ]
            ),
            traffic_group=dict(),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            route_domain=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_one_of = [
            ['name', 'address']
        ]
        self.mutually_exclusive = [
            ['use_route_advertisement', 'route_advertisement']
        ]


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
