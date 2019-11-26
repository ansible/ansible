#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_remote_user
short_description: Manages default settings for remote user accounts on a BIG-IP
description:
  - Manages default settings for remote user accounts on a BIG-IP.
version_added: 2.9
options:
  default_role:
    description:
      - Specifies the default role for all remote user accounts.
      - The default system value is C(no-access).
    type: str
    choices:
      - acceleration-policy-editor
      - admin
      - application-editor
      - auditor
      - certificate-manager
      - firewall-manager
      - fraud-protection-manager
      - guest
      - irule-manager
      - manager
      - no-access
      - operator
      - resource-admin
      - user-manager
      - web-application-security-administrator
      - web-application-security-editor
  default_partition:
    description:
      - Specifies the default partition for all remote user accounts.
      - The default system value is C(all) for all partitions.
    type: str
  console_access:
    description:
      - Enables or disables the default console access for all remote user accounts.
      - The default system value is C(disabled).
    type: bool
  description:
    description:
      - User defined description.
    type: str
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Modify default partition and console access
  bigip_remote_user:
    default_partition: Common
    console_access: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Modify default role, partition and console access
  bigip_remote_user:
    default_partition: Common
    default_role: manager
    console_access: yes
    description: "Changed new settings"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Revert to default settings
  bigip_remote_user:
    default_partition: all
    default_role: "no-access"
    console_access: no
    description: ""
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
default_role:
  description: The default role for all remote user accounts.
  returned: changed
  type: str
  sample: auditor
default_partition:
  description: The default partition for all remote user accounts.
  returned: changed
  type: str
  sample: Common
console_access:
  description: The default console access for all remote user accounts
  returned: changed
  type: bool
  sample: no
description:
  description: The user defined description.
  returned: changed
  type: str
  sample: Foo is bar
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
    from library.module_utils.network.f5.compare import cmp_str_with_none
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean
    from ansible.module_utils.network.f5.compare import cmp_str_with_none


class Parameters(AnsibleF5Parameters):
    api_map = {
        'defaultPartition': 'default_partition',
        'defaultRole': 'default_role',
        'remoteConsoleAccess': 'console_access',
    }

    api_attributes = [
        'defaultPartition',
        'defaultRole',
        'description',
        'remoteConsoleAccess',

    ]

    returnables = [
        'default_partition',
        'default_role',
        'console_access',
        'description',
    ]

    updatables = [
        'default_partition',
        'default_role',
        'console_access',
        'description',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    @property
    def console_access(self):
        result = flatten_boolean(self._values['console_access'])
        if result == 'yes':
            return 'tmsh'
        if result == 'no':
            return 'disabled'


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
    pass


class ReportableChanges(Changes):
    @property
    def console_access(self):
        if self._values['console_access'] is None:
            return None
        if self._values['console_access'] == 'tmsh':
            return 'yes'
        if self._values['console_access'] == 'disabled':
            return 'no'


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
    def description(self):
        result = cmp_str_with_none(self.want.description, self.have.description)
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

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
        result = dict()

        changed = self.update()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
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
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-user/".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
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
        uri = "https://{0}:{1}/mgmt/tm/auth/remote-user/".format(
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
        return ApiParameters(params=response)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.choices = [
            'acceleration-policy-editor',
            'admin',
            'application-editor',
            'auditor',
            'certificate-manager',
            'firewall-manager',
            'fraud-protection-manager',
            'guest',
            'irule-manager',
            'manager',
            'no-access',
            'operator',
            'resource-admin',
            'user-manager',
            'web-application-security-administrator',
            'web-application-security-editor'
        ]
        argument_spec = dict(
            default_role=dict(
                choices=self.choices
            ),
            default_partition=dict(),
            console_access=dict(type='bool'),
            description=dict()
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_one_of = [
            ['default_role', 'default_partition']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
