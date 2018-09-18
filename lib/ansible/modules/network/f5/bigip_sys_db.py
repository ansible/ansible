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
version_added: 2.2
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
    default: present
    choices:
      - present
      - reset
  value:
    description:
      - The value to set the key to. At least one of value and state C(reset)
        are required.
notes:
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
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

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
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
    from ansible.module_utils.network.f5.common import f5_argument_spec

    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
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

    @property
    def name(self):
        return self._values['key']

    @name.setter
    def name(self, value):
        self._values['key'] = value


class Changes(Parameters):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if self.want.state == 'reset':
            if str(self.have.value) != str(self.have.default_value):
                changed[self.want.key] = self.have.default_value
        if changed:
            self.changes = Changes(params=changed)
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
        return Parameters(params=result)

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
        if self.module.check_mode:
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
        if self.module.check_mode:
            return True
        self.reset_on_device()
        self.want.update({'key': self.want.key})
        self.want.update({'value': self.have.default_value})
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
        resource.update(value=self.have.default_value)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            key=dict(required=True),
            state=dict(
                default='present',
                choices=['present', 'reset']
            ),
            value=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

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
