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
    required: True
  vlans:
    description:
      - VLANs that the guest uses to communicate with other guests, the host, and with
        the external network. The available VLANs in the list are those that are
        currently configured on the vCMP host.
      - The order of these VLANs is not important; in fact, it's ignored. This module will
        order the VLANs for you automatically. Therefore, if you deliberately re-order them
        in subsequent tasks, you will find that this module will B(not) register a change.
  initial_image:
    description:
      - Specifies the base software release ISO image file for installing the TMOS
        hypervisor instance and any licensed BIG-IP modules onto the guest's virtual
        disk. When creating a new guest, this parameter is required.
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
  mgmt_route:
    description:
      - Specifies the gateway address for the C(mgmt_address).
      - If this value is not specified when creating a new guest, it is set to C(none).
      - The value C(none) can be used during an update to remove this value.
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
    default: "present"
    choices:
      - configured
      - disabled
      - provisioned
      - present
      - absent
  cores_per_slot:
    description:
      - Specifies the number of cores that the system allocates to the guest.
      - Each core represents a portion of CPU and memory. Therefore, the amount of
        memory allocated per core is directly tied to the amount of CPU. This amount
        of memory varies per hardware platform type.
      - The number you can specify depends on the type of hardware you have.
      - In the event of a reboot, the system persists the guest to the same slot on
        which it ran prior to the reboot.
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
notes:
  - This module can take a lot of time to deploy vCMP guests. This is an intrinsic
    limitation of the vCMP system because it is booting real VMs on the BIG-IP
    device. This boot time is very similar in length to the time it takes to
    boot VMs on any other virtualization platform; public or private.
  - When BIG-IP starts, the VMs are booted sequentially; not in parallel. This
    means that it is not unusual for a vCMP host with many guests to take a
    long time (60+ minutes) to reboot and bring all the guests online. The
    BIG-IP chassis will be available before all vCMP guests are online.
  - netaddr
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a vCMP guest
  bigip_vcmp_guest:
    name: foo
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
    mgmt_network: bridge
    mgmt_address: 10.20.30.40/24
  delegate_to: localhost

- name: Create a vCMP guest with specific VLANs
  bigip_vcmp_guest:
    name: foo
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
    mgmt_network: bridge
    mgmt_address: 10.20.30.40/24
    vlans:
      - vlan1
      - vlan2
  delegate_to: localhost

- name: Remove vCMP guest and disk
  bigip_vcmp_guest:
    name: guest1
    state: absent
    delete_virtual_disk: yes
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
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from f5.utils.responses.handlers import Stats
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
        from f5.utils.responses.handlers import Stats
    except ImportError:
        HAS_F5SDK = False

try:
    from netaddr import IPAddress, AddrFormatError, IPNetwork
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'managementGw': 'mgmt_route',
        'managementNetwork': 'mgmt_network',
        'managementIp': 'mgmt_address',
        'initialImage': 'initial_image',
        'virtualDisk': 'virtual_disk',
        'coresPerSlot': 'cores_per_slot'
    }

    api_attributes = [
        'vlans', 'managementNetwork', 'managementIp', 'initialImage', 'managementGw',
        'state'
    ]

    returnables = [
        'vlans', 'mgmt_network', 'mgmt_address', 'initial_image', 'mgmt_route',
        'name'
    ]

    updatables = [
        'vlans', 'mgmt_network', 'mgmt_address', 'initial_image', 'mgmt_route',
        'state'
    ]

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    @property
    def mgmt_route(self):
        if self._values['mgmt_route'] is None:
            return None
        elif self._values['mgmt_route'] == 'none':
            return 'none'
        try:
            result = IPAddress(self._values['mgmt_route'])
            return str(result)
        except AddrFormatError:
            raise F5ModuleError(
                "The specified 'mgmt_route' is not a valid IP address"
            )

    @property
    def mgmt_address(self):
        if self._values['mgmt_address'] is None:
            return None
        try:
            addr = IPNetwork(self._values['mgmt_address'])
            result = '{0}/{1}'.format(addr.ip, addr.prefixlen)
            return result
        except AddrFormatError:
            raise F5ModuleError(
                "The specified 'mgmt_address' is not a valid IP address"
            )

    @property
    def mgmt_tuple(self):
        result = None
        Destination = namedtuple('Destination', ['ip', 'subnet'])
        try:
            parts = self._values['mgmt_address'].split('/')
            if len(parts) == 2:
                result = Destination(ip=parts[0], subnet=parts[1])
            elif len(parts) < 2:
                result = Destination(ip=parts[0], subnet=None)
            else:
                F5ModuleError(
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
            "The specified 'initial_image' does not exist on the remote device"
        )

    def initial_image_exists(self, image):
        collection = self.client.api.tm.sys.software.images.get_collection()
        for resource in collection:
            if resource.name.startswith(image):
                return True
        return False


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
    def mgmt_address(self):
        want = self.want.mgmt_tuple
        if want.subnet is None:
            raise F5ModuleError(
                "A subnet must be specified when changing the mgmt_address"
            )
        if self.want.mgmt_address != self.have.mgmt_address:
            return self.want.mgmt_address


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = Parameters(client=self.client, params=self.module.params)
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
                changed[k] = change
        if changed:
            self.changes = Parameters(params=changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['configured', 'provisioned', 'deployed']:
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
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

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        result = self.client.api.tm.vcmp.guests.guest.exists(
            name=self.want.name
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
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

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.vcmp.guests.guest.create(
            name=self.want.name,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.vcmp.guests.guest.load(
            name=self.want.name
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.vcmp.guests.guest.load(
            name=self.want.name
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.vcmp.guests.guest.load(
            name=self.want.name
        )
        result = resource.attrs
        return Parameters(params=result)

    def remove_virtual_disk(self):
        if self.virtual_disk_exists():
            return self.remove_virtual_disk_from_device()
        return False

    def virtual_disk_exists(self):
        collection = self.client.api.tm.vcmp.virtual_disks.get_collection()
        for resource in collection:
            check = '{0}/'.format(self.have.virtual_disk)
            if resource.name.startswith(check):
                return True
        return False

    def remove_virtual_disk_from_device(self):
        collection = self.client.api.tm.vcmp.virtual_disks.get_collection()
        for resource in collection:
            check = '{0}/'.format(self.have.virtual_disk)
            if resource.name.startswith(check):
                resource.delete()
                return True
        return False

    def is_configured(self):
        """Checks to see if guest is disabled

        A disabled guest is fully disabled once their Stats go offline.
        Until that point they are still in the process of disabling.

        :return:
        """
        try:
            res = self.client.api.tm.vcmp.guests.guest.load(name=self.want.name)
            Stats(res.stats.load())
            return False
        except iControlUnexpectedHTTPError as ex:
            if 'Object not found - ' in str(ex):
                return True
            raise

    def is_provisioned(self):
        try:
            res = self.client.api.tm.vcmp.guests.guest.load(name=self.want.name)
            stats = Stats(res.stats.load())
            if stats.stat['requestedState']['description'] == 'provisioned':
                if stats.stat['vmStatus']['description'] == 'stopped':
                    return True
        except iControlUnexpectedHTTPError:
            pass
        return False

    def is_deployed(self):
        try:
            res = self.client.api.tm.vcmp.guests.guest.load(name=self.want.name)
            stats = Stats(res.stats.load())
            if stats.stat['requestedState']['description'] == 'deployed':
                if stats.stat['vmStatus']['description'] == 'running':
                    return True
        except iControlUnexpectedHTTPError:
            pass
        return False

    def configure(self):
        if self.is_configured():
            return False
        self.configure_on_device()
        self.wait_for_configured()
        return True

    def configure_on_device(self):
        resource = self.client.api.tm.vcmp.guests.guest.load(name=self.want.name)
        resource.modify(state='configured')

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
        resource = self.client.api.tm.vcmp.guests.guest.load(name=self.want.name)
        resource.modify(state='provisioned')

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
        resource = self.client.api.tm.vcmp.guests.guest.load(name=self.want.name)
        resource.modify(state='deployed')

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
            state=dict(
                default='present',
                choices=['configured', 'disabled', 'provisioned', 'absent', 'present']
            ),
            delete_virtual_disk=dict(
                type='bool', default='no'
            ),
            cores_per_slot=dict(type='int'),
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
