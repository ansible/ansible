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
module: bigip_sys_db
short_description: Manage BIG-IP system database variables
description:
  - Manage BIG-IP system database variables
version_added: "2.2"
options:
  key:
    description:
      - The database variable to manipulate.
    required: True
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value). When C(reset) sets the
        variable back to the default value. At least one of value and state
        C(reset) are required.
    required: False
    default: present
    choices:
      - present
      - reset
  value:
    description:
      - The value to set the key to. At least one of value and state C(reset)
        are required.
    required: False
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set the boot.quiet DB variable on the BIG-IP
  bigip_sys_db:
    user: admin
    password: secret
    server: lb.mydomain.com
    key: boot.quiet
    value: disable
  delegate_to: localhost

- name: Disable the initial setup screen
  bigip_sys_db:
    user: admin
    password: secret
    server: lb.mydomain.com
    key: setup.run
    value: false
  delegate_to: localhost

- name: Reset the initial setup screen
  bigip_sys_db:
    user: admin
    password: secret
    server: lb.mydomain.com
    key: setup.run
    state: reset
  delegate_to: localhost
'''

RETURN = r'''
name:
  description: The key in the system database that was specified
  returned: changed and success
  type: string
  sample: setup.run
default_value:
  description: The default value of the key
  returned: changed and success
  type: string
  sample: true
value:
  description: The value that you set the key to
  returned: changed and success
  type: string
  sample: false
'''

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultValue': 'default_value'
    }
    api_attributes = ['value']
    updatables = ['value']
    returnables = ['name', 'value', 'default_value']

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
    def name(self):
        return self._values['key']

    @name.setter
    def name(self, value):
        self._values['key'] = value


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if self.want.state == 'reset':
            if str(self.want.value) == str(self.want.default_value):
                changed[self.want.key] = self.want.value
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
            elif state == "reset":
                changed = self.reset()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name=self.want.key
        )
        result = resource.attrs
        return Parameters(result)

    def exists(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name=self.want.key
        )
        if str(resource.value) == str(self.want.value):
            return True
        return False

    def present(self):
        if self.exists():
            return False
        else:
            return self.update()

    def update(self):
        if self.want.value is None:
            raise F5ModuleError(
                "When setting a key, a value must be supplied"
            )
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.sys.dbs.db.load(
            name=self.want.key
        )
        resource.update(**params)

    def reset(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError(
                "Failed to reset the DB variable"
            )

    def reset_on_device(self):
        resource = self.client.api.tm.sys.dbs.db.load(
            name=self.want.key
        )
        resource.update(value=self.want.default_value)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            key=dict(required=True),
            state=dict(
                default='present',
                choices=['present', 'reset']
            ),
            value=dict()
        )
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
