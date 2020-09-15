#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

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
    type: str
    version_added: 2.6
  address:
    description:
      - Virtual address. This value cannot be modified after it is set.
      - If you never created a virtual address, but did create virtual servers, then
        a virtual address for each virtual server was created automatically. The name
        of this virtual address is its IP address value.
    type: str
  netmask:
    description:
      - Netmask of the provided virtual address. This value cannot be
        modified after it is set.
      - When creating a new virtual address, if this parameter is not specified, the
        default value is C(255.255.255.255) for IPv4 addresses and
        C(ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff) for IPv6 addresses.
    type: str
  connection_limit:
    description:
      - Specifies the number of concurrent connections that the system
        allows on this virtual address.
    type: int
  arp_state:
    description:
      - Specifies whether the system accepts ARP requests. When (disabled),
        specifies that the system does not accept ARP requests. Note that
        both ARP and ICMP Echo must be disabled in order for forwarding
        virtual servers using that virtual address to forward ICMP packets.
        If (enabled), then the packets are dropped.
      - Deprecated. Use the C(arp) parameter instead.
      - When creating a new virtual address, if this parameter is not specified,
        the default value is C(enabled).
    type: str
    choices:
      - enabled
      - disabled
  arp:
    description:
      - Specifies whether the system accepts ARP requests.
      - When C(no), specifies that the system does not accept ARP requests.
      - When C(yes), then the packets are dropped.
      - Note that both ARP and ICMP Echo must be disabled in order for forwarding
        virtual servers using that virtual address to forward ICMP packets.
      - When creating a new virtual address, if this parameter is not specified,
        the default value is C(yes).
    type: bool
    version_added: 2.7
  auto_delete:
    description:
      - Specifies whether the system automatically deletes the virtual
        address with the deletion of the last associated virtual server.
        When C(disabled), specifies that the system leaves the virtual
        address even when all associated virtual servers have been deleted.
        When creating the virtual address, the default value is C(enabled).
      - C(enabled) and C(disabled) are deprecated and will be removed in
        Ansible 2.11. Instead, use known Ansible booleans such as C(yes) and
        C(no)
    type: str
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
    type: str
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
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
  availability_calculation:
    description:
      - Specifies what routes of the virtual address the system advertises.
        When C(when_any_available), advertises the route when any virtual
        server is available. When C(when_all_available), advertises the
        route when all virtual servers are available. When (always), always
        advertises the route regardless of the virtual servers available.
    type: str
    choices:
      - always
      - when_all_available
      - when_any_available
    aliases: ['advertise_route']
    version_added: 2.6
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
    type: str
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
    type: str
    default: Common
    version_added: 2.5
  traffic_group:
    description:
      - The traffic group for the virtual address. When creating a new address,
        if this value is not specified, the default of C(/Common/traffic-group-1)
        will be used.
    type: str
    version_added: 2.5
  route_domain:
    description:
      - The route domain of the C(address) that you want to use.
      - This value cannot be modified after it is set.
    type: str
    version_added: 2.6
  spanning:
    description:
      - Enables all BIG-IP systems in a device group to listen for and process traffic
        on the same virtual address.
      - Spanning for a virtual address occurs when you enable the C(spanning) option on a
        device and then sync the virtual address to the other members of the device group.
      - Spanning also relies on the upstream router to distribute application flows to the
        BIG-IP systems using ECMP routes. ECMP defines a route to the virtual address using
        distinct Floating self-IP addresses configured on each BIG-IP system.
      - You must also configure MAC masquerade addresses and disable C(arp) on the virtual
        address when Spanning is enabled.
      - When creating a new virtual address, if this parameter is not specified, the default
        valus is C(no).
    version_added: 2.7
    type: bool
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Add virtual address
  bigip_virtual_address:
    state: present
    partition: Common
    address: 10.10.10.10
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost

- name: Enable route advertisement on the virtual address
  bigip_virtual_address:
    state: present
    address: 10.10.10.10
    route_advertisement: any
    provider:
      server: lb.mydomain.net
      user: admin
      password: secret
  delegate_to: localhost
'''

RETURN = r'''
availability_calculation:
  description: Specifies what routes of the virtual address the system advertises.
  returned: changed
  type: str
  sample: always
auto_delete:
  description: New setting for auto deleting virtual address.
  returned: changed
  type: str
  sample: enabled
icmp_echo:
  description: New ICMP echo setting applied to virtual address.
  returned: changed
  type: str
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
arp:
  description: The new way the virtual address handles ARP requests.
  returned: changed
  type: bool
  sample: yes
address:
  description: The address of the virtual address.
  returned: created
  type: int
  sample: 2345
state:
  description: The new state of the virtual address.
  returned: changed
  type: str
  sample: disabled
spanning:
  description: Whether spanning is enabled or not
  returned: changed
  type: str
  sample: disabled
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE
from distutils.version import LooseVersion

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.network.f5.ipaddress import compress_address
    from library.module_utils.network.f5.icontrol import tmos_version
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.network.f5.ipaddress import compress_address
    from ansible.module_utils.network.f5.icontrol import tmos_version


class Parameters(AnsibleF5Parameters):
    api_map = {
        'routeAdvertisement': 'route_advertisement_type',
        'autoDelete': 'auto_delete',
        'icmpEcho': 'icmp_echo',
        'connectionLimit': 'connection_limit',
        'serverScope': 'availability_calculation',
        'mask': 'netmask',
        'trafficGroup': 'traffic_group',
    }

    updatables = [
        'route_advertisement_type',
        'auto_delete',
        'icmp_echo',
        'connection_limit',
        'arp',
        'enabled',
        'availability_calculation',
        'traffic_group',
        'spanning',
    ]

    returnables = [
        'route_advertisement_type',
        'auto_delete',
        'icmp_echo',
        'connection_limit',
        'netmask',
        'arp',
        'address',
        'state',
        'traffic_group',
        'route_domain',
        'spanning',
        'availability_calculation',
    ]

    api_attributes = [
        'routeAdvertisement',
        'autoDelete',
        'icmpEcho',
        'connectionLimit',
        'advertiseRoute',
        'arp',
        'mask',
        'enabled',
        'serverScope',
        'trafficGroup',
        'spanning',
        'serverScope',
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
        if is_valid_ip(self._values['netmask']):
            return self._values['netmask']
        else:
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
        if self.route_advertisement:
            return self.route_advertisement
        else:
            return self._values['route_advertisement_type']

    @property
    def route_advertisement(self):
        if self._values['route_advertisement'] is None:
            return None
        version = tmos_version(self.client)
        if LooseVersion(version) <= LooseVersion('13.0.0'):
            if self._values['route_advertisement'] == 'disabled':
                return 'disabled'
            else:
                return 'enabled'
        else:
            return self._values['route_advertisement']


class ApiParameters(Parameters):
    @property
    def arp(self):
        if self._values['arp'] is None:
            return None
        elif self._values['arp'] == 'enabled':
            return True
        return False

    @property
    def spanning(self):
        if self._values['spanning'] is None:
            return None
        if self._values['spanning'] == 'enabled':
            return True
        return False


class ModuleParameters(Parameters):
    @property
    def arp(self):
        if self._values['arp'] is None:
            if self.arp_state and self.arp_state == 'enabled':
                return True
            elif self.arp_state and self.arp_state == 'disabled':
                return False
        else:
            return self._values['arp']

    @property
    def address(self):
        if self._values['address'] is None:
            return None
        if is_valid_ip(self._values['address']):
            return compress_address(self._values['address'])
        else:
            raise F5ModuleError(
                "The provided 'address' is not a valid IP address"
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

    @property
    def route_domain(self):
        if self._values['route_domain'] is None:
            return None
        try:
            return int(self._values['route_domain'])
        except ValueError:
            uri = "https://{0}:{1}/mgmt/tm/net/route-domain/{2}".format(
                self.client.provider['server'],
                self.client.provider['server_port'],
                transform_name(self._values['partition'], self._values['route_domain'])
            )
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError:
                raise F5ModuleError(
                    "The specified 'route_domain' was not found."
                )
            if resp.status == 404 or 'code' in response and response['code'] == 404:
                raise F5ModuleError(
                    "The specified 'route_domain' was not found."
                )

            return int(response['id'])


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    @property
    def address(self):
        if self._values['address'] is None:
            return None
        if self._values['route_domain'] is None:
            return self._values['address']
        result = "{0}%{1}".format(self._values['address'], self.route_domain)
        return result

    @property
    def arp(self):
        if self._values['arp'] is None:
            return None
        elif self._values['arp'] is True:
            return 'enabled'
        elif self._values['arp'] is False:
            return 'disabled'

    @property
    def spanning(self):
        if self._values['spanning'] is None:
            return None
        if self._values['spanning']:
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def arp(self):
        if self._values['arp'] == 'disabled':
            return 'no'
        elif self._values['arp'] == 'enabled':
            return 'yes'


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

    @property
    def spanning(self):
        if self.want.spanning is None:
            return None
        if self.want.spanning != self.have.spanning:
            return self.want.spanning

    @property
    def arp_state(self):
        if self.want.arp_state is None:
            return None
        if self.want.arp_state != self.have.arp_state:
            return self.want.arp_state


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.have = ApiParameters()
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

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state in ['present', 'enabled', 'disabled']:
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)

        if self.module._diff and self.have:
            result['diff'] = self.make_diff()

        result.update(dict(changed=changed))
        self._announce_deprecations(result)

        return result

    def _grab_attr(self, item):
        result = dict()
        updatables = Parameters.updatables
        for k in updatables:
            if getattr(item, k) is not None:
                result[k] = getattr(item, k)
        return result

    def make_diff(self):
        result = dict(before=self._grab_attr(self.have), after=self._grab_attr(self.want))
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

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the virtual address")
        return True

    def create(self):
        self._set_changed_options()

        if self.want.traffic_group is None:
            self.want.update({'traffic_group': '/Common/traffic-group-1'})
        if self.want.arp is None:
            self.want.update({'arp': True})
        if self.want.spanning is None:
            self.want.update({'spanning': False})

        if self.want.netmask is None:
            if is_valid_ip(self.want.address, type='ipv4'):
                self.want.update({'netmask': '255.255.255.255'})
            else:
                self.want.update({'netmask': 'ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff'})

        if self.want.arp and self.want.spanning:
            raise F5ModuleError(
                "'arp' and 'spanning' cannot both be enabled on virtual address."
            )
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the virtual address")

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
        if self.changes.arp and self.changes.spanning:
            raise F5ModuleError(
                "'arp' and 'spanning' cannot both be enabled on virtual address."
            )

        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual-address/{2}".format(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual-address/{2}".format(
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual-address/{2}".format(
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

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        params['address'] = self.changes.address
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual-address/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] in [400, 403, 409]:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        return response['selfLink']

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/ltm/virtual-address/{2}".format(
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
            state=dict(
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
            ),
            name=dict(),
            address=dict(),
            netmask=dict(),
            connection_limit=dict(
                type='int'
            ),

            auto_delete=dict(),
            icmp_echo=dict(
                choices=['enabled', 'disabled', 'selective'],
            ),
            availability_calculation=dict(
                choices=['always', 'when_all_available', 'when_any_available'],
                aliases=['advertise_route']
            ),
            traffic_group=dict(),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            ),
            route_domain=dict(),
            spanning=dict(type='bool'),
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

            # Deprecated pair - ARP
            arp_state=dict(
                choices=['enabled', 'disabled'],
                removed_in_version=2.11,
            ),
            arp=dict(type='bool'),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_one_of = [
            ['name', 'address']
        ]
        self.mutually_exclusive = [
            ['arp_state', 'arp']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
        required_one_of=spec.required_one_of
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
