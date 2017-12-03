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
module: bigip_vlan
short_description: Manage VLANs on a BIG-IP system
description:
  - Manage VLANs on a BIG-IP system
version_added: "2.2"
options:
  description:
    description:
      - The description to give to the VLAN.
  tagged_interfaces:
    description:
      - Specifies a list of tagged interfaces and trunks that you want to
        configure for the VLAN. Use tagged interfaces or trunks when
        you want to assign a single interface or trunk to multiple VLANs.
    aliases:
      - tagged_interface
  untagged_interfaces:
    description:
      - Specifies a list of untagged interfaces and trunks that you want to
        configure for the VLAN.
    aliases:
      - untagged_interface
  name:
    description:
      - The VLAN to manage. If the special VLAN C(ALL) is specified with
        the C(state) value of C(absent) then all VLANs will be removed.
    required: True
  state:
    description:
      - The state of the VLAN on the system. When C(present), guarantees
        that the VLAN exists with the provided attributes. When C(absent),
        removes the VLAN from the system.
    default: present
    choices:
      - absent
      - present
  tag:
    description:
      - Tag number for the VLAN. The tag number can be any integer between 1
        and 4094. The system automatically assigns a tag number if you do not
        specify a value.
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires BIG-IP versions >= 12.0.0
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create VLAN
  bigip_vlan:
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Set VLAN tag
  bigip_vlan:
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "2345"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Add VLAN 2345 as tagged to interface 1.1
  bigip_vlan:
      tagged_interface: 1.1
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "2345"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Add VLAN 1234 as tagged to interfaces 1.1 and 1.2
  bigip_vlan:
      tagged_interfaces:
          - 1.1
          - 1.2
      name: "net1"
      password: "secret"
      server: "lb.mydomain.com"
      tag: "1234"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost
'''

RETURN = r'''
description:
    description: The description set on the VLAN
    returned: changed
    type: string
    sample: foo VLAN
interfaces:
    description: Interfaces that the VLAN is assigned to
    returned: changed
    type: list
    sample: ['1.1','1.2']
name:
    description: The name of the VLAN
    returned: changed
    type: string
    sample: net1
partition:
    description: The partition that the VLAN was created on
    returned: changed
    type: string
    sample: Common
tag:
    description: The ID of the VLAN
    returned: changed
    type: int
    sample: 2345
'''

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        if params:
            self.update(params=params)

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
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    updatables = [
        'tagged_interfaces', 'untagged_interfaces', 'tag',
        'description'
    ]

    returnables = [
        'description', 'partition', 'name', 'tag', 'interfaces',
        'tagged_interfaces', 'untagged_interfaces'
    ]

    api_attributes = [
        'description', 'interfaces', 'partition', 'name', 'tag'
    ]
    api_map = {}

    @property
    def interfaces(self):
        tagged = self._values['tagged_interfaces']
        untagged = self._values['untagged_interfaces']
        if tagged:
            return [dict(name=x, tagged=True) for x in tagged]
        if untagged:
            return [dict(name=x, untagged=True) for x in untagged]

    @property
    def tagged_interfaces(self):
        value = self._values['tagged_interfaces']
        if value is None:
            return None
        ifcs = self._parse_return_ifcs()
        for ifc in value:
            if ifc not in ifcs:
                err = 'The specified interface "%s" was not found' % ifc
                raise F5ModuleError(err)
        return value

    @property
    def untagged_interfaces(self):
        value = self._values['untagged_interfaces']
        if value is None:
            return None
        ifcs = self._parse_return_ifcs()
        for ifc in value:
            if ifc not in ifcs:
                err = 'The specified interface "%s" was not found' % ifc
                raise F5ModuleError(err)
        return value

    def _get_interfaces_from_device(self):
        lst = self.client.api.tm.net.interfaces.get_collection()
        return lst

    def _parse_return_ifcs(self):
        ifclst = self._get_interfaces_from_device()
        ifcs = [str(x.name) for x in ifclst]
        if not ifcs:
            err = 'No interfaces were found'
            raise F5ModuleError(err)
        return ifcs

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if api_attribute in self.api_map:
                result[api_attribute] = getattr(
                    self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters()
        self.want.client = self.client
        self.want.update(self.client.module.params)
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
        return result

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

    def _have_interfaces(self, ifcs):
        untagged = [str(x.name) for x in ifcs if hasattr(x, 'untagged')]
        tagged = [str(x.name) for x in ifcs if hasattr(x, 'tagged')]
        if untagged:
            self.have.update({'untagged_interfaces': untagged})
        if tagged:
            self.have.update({'tagged_interfaces': tagged})

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
        self.have, ifcs = self.read_current_from_device()
        if ifcs:
            self._have_interfaces(ifcs)
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
            raise F5ModuleError("Failed to delete the VLAN")
        return True

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.net.vlans.vlan.create(**params)

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.net.vlans.vlan.load(
            name=self.want.name, partition=self.want.partition
        )
        result.modify(**params)

    def exists(self):
        return self.client.api.tm.net.vlans.vlan.exists(
            name=self.want.name, partition=self.want.partition
        )

    def remove_from_device(self):
        result = self.client.api.tm.net.vlans.vlan.load(
            name=self.want.name, partition=self.want.partition
        )
        if result:
            result.delete()

    def read_current_from_device(self):
        tmp_res = self.client.api.tm.net.vlans.vlan.load(
            name=self.want.name, partition=self.want.partition
        )
        ifcs = tmp_res.interfaces_s.get_collection()

        result = tmp_res.attrs
        return Parameters(result), ifcs


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(
                required=True,
            ),
            tagged_interfaces=dict(
                type='list',
                aliases=['tagged_interface']
            ),
            untagged_interfaces=dict(
                type='list',
                aliases=['untagged_interface']
            ),
            description=dict(),
            tag=dict(
                type='int'
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
        f5_product_name=spec.f5_product_name,
        mutually_exclusive=[
            ['tagged_interfaces', 'untagged_interfaces']
        ]
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
