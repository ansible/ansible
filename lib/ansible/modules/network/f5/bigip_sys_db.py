#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

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
    type: str
    required: True
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value). When C(reset) sets the
        variable back to the default value. At least one of value and state
        C(reset) are required.
    type: str
    choices:
      - present
      - reset
    default: present
  value:
    description:
      - The value to set the key to. At least one of value and state C(reset)
        are required.
    type: str
notes:
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set the boot.quiet DB variable on the BIG-IP
  bigip_sys_db:
    key: boot.quiet
    value: disable
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Disable the initial setup screen
  bigip_sys_db:
    key: setup.run
    value: false
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost

- name: Reset the initial setup screen
  bigip_sys_db:
    key: setup.run
    state: reset
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
name:
  description: The key in the system database that was specified
  returned: changed and success
  type: str
  sample: setup.run
default_value:
  description: The default value of the key
  returned: changed and success
  type: str
  sample: true
value:
  description: The value that you set the key to
  returned: changed and success
  type: str
  sample: false
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultValue': 'default_value'
    }
    api_attributes = [
        'value',
    ]
    updatables = [
        'value',
    ]
    returnables = [
        'name',
        'value',
        'default_value',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


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
    def value(self):
        if self.want.state == 'reset':
            if str(self.have.value) != str(self.have.default_value):
                return self.have.default_value
        if self.want.value != self.have.value:
            return self.want.value


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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
            changed['name'] = self.want.key
            changed['default_value'] = self.have.default_value
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "reset":
            changed = self.reset()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        if self.exists():
            return False
        else:
            return self.update()

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

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.key
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))
        if str(response['value']) == str(self.want.value):
            return True
        return False

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.key
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
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.key
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

    def reset_on_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/db/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.key
        )
        params = dict(
            value=self.have.default_value
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
