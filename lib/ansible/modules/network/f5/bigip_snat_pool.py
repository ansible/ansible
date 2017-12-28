#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_snat_pool
short_description: Manage SNAT pools on a BIG-IP
description:
  - Manage SNAT pools on a BIG-IP.
version_added: "2.3"
options:
  members:
    description:
      - List of members to put in the SNAT pool. When a C(state) of present is
        provided, this parameter is required. Otherwise, it is optional.
    aliases:
      - member
  name:
    description: The name of the SNAT pool.
    required: True
  state:
    description:
      - Whether the SNAT pool should exist or not.
    default: present
    choices:
      - present
      - absent
  partition:
    description:
      - Device partition to manage resources on.
    default: 'Common'
    version_added: 2.5
notes:
   - Requires the f5-sdk Python package on the host. This is as easy as
     pip install f5-sdk
   - Requires the netaddr Python package on the host. This is as easy as
     pip install netaddr
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add the SNAT pool 'my-snat-pool'
  bigip_snat_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my-snat-pool
    state: present
    members:
      - 10.10.10.10
      - 20.20.20.20
  delegate_to: localhost

- name: Change the SNAT pool's members to a single member
  bigip_snat_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: my-snat-pool
    state: present
    member: 30.30.30.30
  delegate_to: localhost

- name: Remove the SNAT pool 'my-snat-pool'
  bigip_snat_pool:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: johnd
    state: absent
  delegate_to: localhost
'''

RETURN = r'''
members:
  description:
    - List of members that are part of the SNAT pool.
  returned: changed and success
  type: list
  sample: "['10.10.10.10']"
'''

import os

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False

try:
    from netaddr import IPAddress, AddrFormatError
    HAS_NETADDR = True
except ImportError:
    HAS_NETADDR = False


class Parameters(AnsibleF5Parameters):
    api_map = {}

    updatables = [
        'members'
    ]

    returnables = [
        'members'
    ]

    api_attributes = [
        'members'
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
    def members(self):
        if self._values['members'] is None:
            return None
        result = set()
        for member in self._values['members']:
            member = self._clear_member_prefix(member)
            address = self._format_member_address(member)
            result.update([address])
        return list(result)

    def _clear_member_prefix(self, member):
        result = os.path.basename(member)
        return result

    def _format_member_address(self, member):
        try:
            address = str(IPAddress(member))
            address = '/{0}/{1}'.format(self.partition, address)
            return address
        except (AddrFormatError, ValueError):
            raise F5ModuleError(
                'The provided member address is not a valid IP address'
            )


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

    @property
    def members(self):
        if self.want.members is None:
            return None
        if set(self.want.members) == set(self.have.members):
            return None
        result = list(set(self.want.members))
        return result

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1


class ModuleManager(object):
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
            self.changes = Parameters(changed)
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

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations()
        return result

    def _announce_deprecations(self):
        warnings = []
        if self.want:
            warnings += self.want._values.get('__warnings', [])
        if self.have:
            warnings += self.have._values.get('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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
        resource = self.client.api.tm.ltm.snatpools.snatpool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return Parameters(result)

    def exists(self):
        result = self.client.api.tm.ltm.snatpools.snatpool.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

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

    def update_on_device(self):
        params = self.changes.api_params()

        resource = self.client.api.tm.ltm.snatpools.snatpool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        if not self.exists():
            raise F5ModuleError("Failed to create the SNAT pool")
        return True

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.ltm.snatpools.snatpool.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the SNAT pool")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.ltm.snatpools.snatpool.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(required=True),
            members=dict(
                type='list',
                aliases=['member']
            ),
            state=dict(
                default='present',
                choices=['absent', 'present']
            )
        )
        self.required_if = [
            ['state', 'present', ['members']]
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
