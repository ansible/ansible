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
module: bigip_vcmp_guest
short_description: Manages vCMP guests on a BIG-IP
description:
  - Manages vCMP guests on a BIG-IP. This functionality only exists on
    actual hardware and must be enabled by provisioning C(vcmp) with the
    C(bigip_provision) module.
version_added: 2.5
options:
  name:
    description:
      - The name of the vCMP guest to manage.
    type: str
    required: True
  vlans:
    description:
      - VLANs that the guest uses to communicate with other guests, the host, and with
        the external network. The available VLANs in the list are those that are
        currently configured on the vCMP host.
      - The order of these VLANs is not important; in fact, it's ignored. This module will
        order the VLANs for you automatically. Therefore, if you deliberately re-order them
        in subsequent tasks, you will find that this module will B(not) register a change.
    type: list
  initial_image:
    description:
      - Specifies the base software release ISO image file for installing the TMOS
        hypervisor instance and any licensed BIG-IP modules onto the guest's virtual
        disk. When creating a new guest, this parameter is required.
    type: str
  initial_hotfix:
    description:
      - Specifies the hotfix ISO image file which will be applied on top of the base
        image.
    type: str
    version_added: 2.9
  mgmt_network:
    description:
      - Specifies the method by which the management address is used in the vCMP guest.
      - When C(bridged), specifies that the guest can communicate with the vCMP host's
        management network.
      - When C(isolated), specifies that the guest is isolated from the vCMP host's
        management network. In this case, the only way that a guest can communicate
        with the vCMP host is through the console port or through a self IP address
        on the guest that allows traffic through port 22.
      - When C(host only), prevents the guest from installing images and hotfixes other
        than those provided by the hypervisor.
      - If the guest setting is C(isolated) or C(host only), the C(mgmt_address) does
        not apply.
      - Concerning mode changing, changing C(bridged) to C(isolated) causes the vCMP
        host to remove all of the guest's management interfaces from its bridged
        management network. This immediately disconnects the guest's VMs from the
        physical management network. Changing C(isolated) to C(bridged) causes the
        vCMP host to dynamically add the guest's management interfaces to the bridged
        management network. This immediately connects all of the guest's VMs to the
        physical management network. Changing this property while the guest is in the
        C(configured) or C(provisioned) state has no immediate effect.
    type: str
    choices:
      - bridged
      - isolated
      - host only
  delete_virtual_disk:
    description:
      - When C(state) is C(absent), will additionally delete the virtual disk associated
        with the vCMP guest. By default, this value is C(no).
    type: bool
    default: no
  mgmt_address:
    description:
      - Specifies the IP address, and subnet or subnet mask that you use to access
        the guest when you want to manage a module running within the guest. This
        parameter is required if the C(mgmt_network) parameter is C(bridged).
      - When creating a new guest, if you do not specify a network or network mask,
        a default of C(/24) (C(255.255.255.0)) will be assumed.
    type: str
  mgmt_route:
    description:
      - Specifies the gateway address for the C(mgmt_address).
      - If this value is not specified when creating a new guest, it is set to C(none).
      - The value C(none) can be used during an update to remove this value.
    type: str
  state:
    description:
      - The state of the vCMP guest on the system. Each state implies the actions of
        all states before it.
      - When C(configured), guarantees that the vCMP guest exists with the provided
        attributes. Additionally, ensures that the vCMP guest is turned off.
      - When C(disabled), behaves the same as C(configured) the name of this state
        is just a convenience for the user that is more understandable.
      - When C(provisioned), will ensure that the guest is created and installed.
        This state will not start the guest; use C(deployed) for that. This state
        is one step beyond C(present) as C(present) will not install the guest;
        only setup the configuration for it to be installed.
      - When C(present), ensures the guest is properly provisioned and starts
        the guest so that it is in a running state.
      - When C(absent), removes the vCMP from the system.
    type: str
    choices:
      - configured
      - disabled
      - provisioned
      - present
      - absent
    default: present
  cores_per_slot:
    description:
      - Specifies the number of cores that the system allocates to the guest.
      - Each core represents a portion of CPU and memory. Therefore, the amount of
        memory allocated per core is directly tied to the amount of CPU. This amount
        of memory varies per hardware platform type.
      - The number you can specify depends on the type of hardware you have.
      - In the event of a reboot, the system persists the guest to the same slot on
        which it ran prior to the reboot.
    type: int
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
  number_of_slots:
    description:
      - Specifies the number of slots for the system to use for creating the guest.
      - This value dictates how many cores a guest is allocated from each slot that
        it is assigned to.
      - Possible values are dependent on the type of blades being used in this cluster.
      - The default value depends on the type of blades being used in this cluster.
    type: int
    version_added: 2.7
  min_number_of_slots:
    description:
      - Specifies the minimum number of slots that the guest must be assigned to in
        order to deploy.
      - This field dictates the number of slots that the guest must be assigned to.
      - If at the end of any allocation attempt the guest is not assigned to at least
        this many slots, the attempt fails and the change that initiated it is reverted.
      - A guest's C(min_number_of_slots) value cannot be greater than its C(number_of_slots).
    type: int
    version_added: 2.7
  allowed_slots:
    description:
      - Contains those slots that the guest is allowed to be assigned to.
      - When the host determines which slots this guest should be assigned to, only slots
        in this list will be considered.
      - This is a good way to force guests to be assigned only to particular slots, or,
        by configuring disjoint C(allowed_slots) on two guests, that those guests are
        never assigned to the same slot.
      - By default this list includes every available slot in the cluster. This means,
        by default, the guest may be assigned to any slot.
    type: list
    version_added: 2.7
notes:
  - This module can take a lot of time to deploy vCMP guests. This is an intrinsic
    limitation of the vCMP system because it is booting real VMs on the BIG-IP
    device. This boot time is very similar in length to the time it takes to
    boot VMs on any other virtualization platform; public or private.
  - When BIG-IP starts, the VMs are booted sequentially; not in parallel. This
    means that it is not unusual for a vCMP host with many guests to take a
    long time (60+ minutes) to reboot and bring all the guests online. The
    BIG-IP chassis will be available before all vCMP guests are online.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create a vCMP guest
  bigip_vcmp_guest:
    name: foo
    mgmt_network: bridge
    mgmt_address: 10.20.30.40/24
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Create a vCMP guest with specific VLANs
  bigip_vcmp_guest:
    name: foo
    mgmt_network: bridge
    mgmt_address: 10.20.30.40/24
    vlans:
      - vlan1
      - vlan2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove vCMP guest and disk
  bigip_vcmp_guest:
    name: guest1
    state: absent
    delete_virtual_disk: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  register: result
'''

RETURN = r'''
vlans:
  description: The VLANs assigned to the vCMP guest, in their full path format.
  returned: changed
  type: list
  sample: ['/Common/vlan1', '/Common/vlan2']
'''

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
from collections import namedtuple

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.urls import parseStats
    from library.module_utils.network.f5.ipaddress import is_valid_ip
    from library.module_utils.compat.ipaddress import ip_interface
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.urls import parseStats
    from ansible.module_utils.network.f5.ipaddress import is_valid_ip
    from ansible.module_utils.compat.ipaddress import ip_interface


class Parameters(AnsibleF5Parameters):
    api_map = {
        'managementGw': 'mgmt_route',
        'managementNetwork': 'mgmt_network',
        'managementIp': 'mgmt_address',
        'initialImage': 'initial_image',
        'initialHotfix': 'initial_hotfix',
        'virtualDisk': 'virtual_disk',
        'coresPerSlot': 'cores_per_slot',
        'slots': 'number_of_slots',
        'minSlots': 'min_number_of_slots',
        'allowedSlots': 'allowed_slots',
    }

    api_attributes = [
        'vlans',
        'managementNetwork',
        'managementIp',
        'initialImage',
        'initialHotfix',
        'managementGw',
        'state',
        'coresPerSlot',
        'slots',
        'minSlots',
        'allowedSlots',
    ]

    returnables = [
        'vlans',
        'mgmt_network',
        'mgmt_address',
        'initial_image',
        'initial_hotfix',
        'mgmt_route',
        'name',
        'cores_per_slot',
        'number_of_slots',
        'min_number_of_slots',
        'allowed_slots',
    ]

    updatables = [
        'vlans',
        'mgmt_network',
        'mgmt_address',
        'initial_image',
        'initial_hotfix',
        'mgmt_route',
        'state',
        'cores_per_slot',
        'number_of_slots',
        'min_number_of_slots',
        'allowed_slots',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def mgmt_route(self):
        if self._values['mgmt_route'] is None:
            return None
        elif self._values['mgmt_route'] == 'none':
            return 'none'
        if is_valid_ip(self._values['mgmt_route']):
            return self._values['mgmt_route']
        else:
            raise F5ModuleError(
                "The specified 'mgmt_route' is not a valid IP address."
            )

    @property
    def mgmt_address(self):
        if self._values['mgmt_address'] is None:
            return None
        try:
            addr = ip_interface(u'%s' % str(self._values['mgmt_address']))
            return str(addr.with_prefixlen)
        except ValueError:
            raise F5ModuleError(
                "The specified 'mgmt_address' is not a valid IP address."
            )

    @property
    def mgmt_tuple(self):
        Destination = namedtuple('Destination', ['ip', 'subnet'])
        try:
            parts = self._values['mgmt_address'].split('/')
            if len(parts) == 2:
                result = Destination(ip=parts[0], subnet=parts[1])
            elif len(parts) < 2:
                result = Destination(ip=parts[0], subnet=None)
            else:
                raise F5ModuleError(
                    "The provided mgmt_address is malformed."
                )
        except ValueError:
            result = Destination(ip=None, subnet=None)
        return result

    @property
    def state(self):
        if self._values['state'] == 'present':
            return 'deployed'
        elif self._values['state'] in ['configured', 'disabled']:
            return 'configured'
        return self._values['state']

    @property
    def vlans(self):
        if self._values['vlans'] is None:
            return None
        result = [fq_name(self.partition, x) for x in self._values['vlans']]
        result.sort()
        return result

    @property
    def initial_image(self):
        if self._values['initial_image'] is None:
            return None
        if self.initial_image_exists(self._values['initial_image']):
            return self._values['initial_image']
        raise F5ModuleError(
            "The specified 'initial_image' does not exist on the remote device."
        )

    @property
    def initial_hotfix(self):
        if self._values['initial_hotfix'] is None:
            return None
        if self.initial_hotfix_exists(self._values['initial_hotfix']):
            return self._values['initial_hotfix']
        raise F5ModuleError(
            "The specified 'initial_hotfix' does not exist on the remote device."
        )

    def initial_image_exists(self, image):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/image/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        for resource in response['items']:
            if resource['name'].startswith(image):
                return True
        return False

    def initial_hotfix_exists(self, hotfix):
        uri = "https://{0}:{1}/mgmt/tm/sys/software/hotfix/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        for resource in response['items']:
            if resource['name'].startswith(hotfix):
                return True
        return False

    @property
    def allowed_slots(self):
        if self._values['allowed_slots'] is None:
            return None
        result = self._values['allowed_slots']
        result.sort()
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                change = getattr(self, returnable)
                if isinstance(change, dict):
                    result.update(change)
                else:
                    result[returnable] = change
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


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
    def mgmt_address(self):
        want = self.want.mgmt_tuple
        if want.subnet is None:
            raise F5ModuleError(
                "A subnet must be specified when changing the mgmt_address."
            )
        if self.want.mgmt_address != self.have.mgmt_address:
            return self.want.mgmt_address

    @property
    def allowed_slots(self):
        if self.want.allowed_slots is None:
            return None
        if self.have.allowed_slots is None:
            return self.want.allowed_slots
        if set(self.want.allowed_slots) != set(self.have.allowed_slots):
            return self.want.allowed_slots


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(client=self.client, params=self.module.params)
        self.have = None
        self.changes = ReportableChanges()

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
                changed[k] = change
        if changed:
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state in ['configured', 'provisioned', 'deployed']:
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
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

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        if self.changes.cores_per_slot:
            if not self.is_configured():
                self.configure()
        self.update_on_device()
        if self.want.state == 'provisioned':
            self.provision()
        elif self.want.state == 'deployed':
            self.deploy()
        elif self.want.state == 'configured':
            self.configure()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        if self.want.delete_virtual_disk:
            self.have = self.read_current_from_device()
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        if self.want.delete_virtual_disk:
            self.remove_virtual_disk()
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        if self.want.mgmt_tuple.subnet is None:
            self.want.update(dict(
                mgmt_address='{0}/255.255.255.0'.format(self.want.mgmt_tuple.ip)
            ))
        self.create_on_device()
        if self.want.state == 'provisioned':
            self.provision()
        elif self.want.state == 'deployed':
            self.deploy()
        elif self.want.state == 'configured':
            self.configure()
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        return response['selfLink']

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        response = self.client.api.delete(uri)
        if response.status == 200:
            return True
        raise F5ModuleError(response.content)

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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

    def remove_virtual_disk(self):
        if self.virtual_disk_exists():
            return self.remove_virtual_disk_from_device()
        return False

    def get_virtual_disks_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/virtual-disk/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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

        if 'items' in response:
            return response

    def virtual_disk_exists(self):
        """Checks if a virtual disk exists for a guest

        The virtual disk names can differ based on the device vCMP is installed on.
        For instance, on a shuttle-series device with no slots, you will see disks
        that resemble the following

          guest1.img

        On an 8-blade Viprion with slots though, you will see

          guest1.img/1

        The "/1" in this case is the slot that it is a part of. This method looks
        for the virtual-disk without the trailing slot.

        Returns:
            dict
        """
        response = self.get_virtual_disks_on_device()
        check = '{0}'.format(self.have.virtual_disk)
        for resource in response['items']:
            if resource['name'].startswith(check):
                return True
            else:
                return False

    def remove_virtual_disk_from_device(self):
        check = '{0}'.format(self.have.virtual_disk)
        response = self.get_virtual_disks_on_device()
        for resource in response['items']:
            if resource['name'].startswith(check):
                uri = "https://{0}:{1}/mgmt/tm/vcmp/virtual-disk/{2}".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                    resource['name'].replace('/', '~')
                )
                response = self.client.api.delete(uri)

                if response.status == 200:
                    continue
                else:
                    raise F5ModuleError(response.content)

        return True

    def is_configured(self):
        """Checks to see if guest is disabled

        A disabled guest is fully disabled once their Stats go offline.
        Until that point they are still in the process of disabling.

        :return:
        """
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return True

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        return False

    def is_provisioned(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError:
            return False
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False

        result = parseStats(response)

        if 'stats' in result:
            if result['stats']['requestedState'] == 'provisioned':
                if result['stats']['vmStatus'] == 'stopped':
                    return True
        return False

    def is_deployed(self):
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}/stats".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
        )
        resp = self.client.api.get(uri)

        try:
            response = resp.json()
        except ValueError:
            return False
        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp.content)

        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False

        result = parseStats(response)

        if 'stats' in result:
            if result['stats']['requestedState'] == 'deployed':
                if result['stats']['vmStatus'] == 'running':
                    return True
        return False

    def configure(self):
        if self.is_configured():
            return False
        self.configure_on_device()
        self.wait_for_configured()
        return True

    def configure_on_device(self):
        params = dict(state='configured')
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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

    def wait_for_configured(self):
        nops = 0
        while nops < 3:
            if self.is_configured():
                nops += 1
            time.sleep(1)

    def provision(self):
        if self.is_provisioned():
            return False
        self.provision_on_device()
        self.wait_for_provisioned()

    def provision_on_device(self):
        params = dict(state='provisioned')
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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

    def wait_for_provisioned(self):
        nops = 0
        while nops < 3:
            if self.is_provisioned():
                nops += 1
            time.sleep(1)

    def deploy(self):
        if self.is_deployed():
            return False
        self.deploy_on_device()
        self.wait_for_deployed()

    def deploy_on_device(self):
        params = dict(state='deployed')
        uri = "https://{0}:{1}/mgmt/tm/vcmp/guest/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.name
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

    def wait_for_deployed(self):
        nops = 0
        while nops < 3:
            if self.is_deployed():
                nops += 1
            time.sleep(1)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            name=dict(required=True),
            vlans=dict(type='list'),
            mgmt_network=dict(choices=['bridged', 'isolated', 'host only']),
            mgmt_address=dict(),
            mgmt_route=dict(),
            initial_image=dict(),
            initial_hotfix=dict(),
            state=dict(
                default='present',
                choices=['configured', 'disabled', 'provisioned', 'absent', 'present']
            ),
            delete_virtual_disk=dict(
                type='bool',
                default='no'
            ),
            cores_per_slot=dict(type='int'),
            number_of_slots=dict(type='int'),
            min_number_of_slots=dict(type='int'),
            allowed_slots=dict(type='list'),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['mgmt_network', 'bridged', ['mgmt_address']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
