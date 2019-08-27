#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_password_policy
short_description: Manages the authentication password policy on a BIG-IP
description:
  - Manages the authentication password policy on a BIG-IP.
version_added: 2.8
options:
  expiration_warning:
    description:
      - Specifies the number of days before a password expires.
      - Based on this value, the BIG-IP system automatically warns users when their
        password is about to expire.
    type: int
  max_duration:
    description:
      - Specifies the maximum number of days a password is valid.
    type: int
  max_login_failures:
    description:
      - Specifies the number of consecutive unsuccessful login attempts
        that the system allows before locking out the user.
      - Specify zero (0) to disable this parameter.
    type: int
  min_duration:
    description:
      - Specifies the minimum number of days a password is valid.
    type: int
  min_length:
    description:
      - Specifies the minimum number of characters in a valid password.
      - This value must be between 6 and 255.
    type: int
  policy_enforcement:
    description:
      - Enables or disables the password policy on the BIG-IP system.
    type: bool
  required_lowercase:
    description:
      - Specifies the number of lowercase alpha characters that must be
        present in a password for the password to be valid.
    type: int
  required_numeric:
    description:
      - Specifies the number of numeric characters that must be present in
        a password for the password to be valid.
    type: int
  required_special:
    description:
      - Specifies the number of special characters that must be present in
        a password for the password to be valid.
    type: int
  required_uppercase:
    description:
      - Specifies the number of uppercase alpha characters that must be
        present in a password for the password to be valid.
    type: int
  password_memory:
    description:
      - Specifies whether the user has configured the BIG-IP system to
        remember a password on a specific computer and how many passwords
        to remember.
    type: int
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Change password policy to require 2 numeric characters
  bigip_password_policy:
    required_numeric: 2
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
expiration_warning:
  description: The new expiration warning.
  returned: changed
  type: int
  sample: 7
max_duration:
  description: The new max duration.
  returned: changed
  type: int
  sample: 99999
max_login_failures:
  description: The new max login failures.
  returned: changed
  type: int
  sample: 0
min_duration:
  description: The new min duration.
  returned: changed
  type: int
  sample: 0
min_length:
  description: The new min password length.
  returned: changed
  type: int
  sample: 6
policy_enforcement:
  description: The new policy enforcement setting.
  returned: changed
  type: bool
  sample: yes
required_lowercase:
  description: The lowercase requirement.
  returned: changed
  type: int
  sample: 1
required_numeric:
  description: The numeric requirement.
  returned: changed
  type: int
  sample: 2
required_special:
  description: The special character requirement.
  returned: changed
  type: int
  sample: 1
required_uppercase:
  description: The uppercase character requirement.
  returned: changed
  type: int
  sample: 1
password_memory:
  description: The new number of remembered passwords
  returned: changed
  type: int
  sample: 0
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean


class Parameters(AnsibleF5Parameters):
    api_map = {
        'expirationWarning': 'expiration_warning',
        'maxDuration': 'max_duration',
        'maxLoginFailures': 'max_login_failures',
        'minDuration': 'min_duration',
        'minimumLength': 'min_length',
        'passwordMemory': 'password_memory',
        'policyEnforcement': 'policy_enforcement',
        'requiredLowercase': 'required_lowercase',
        'requiredNumeric': 'required_numeric',
        'requiredSpecial': 'required_special',
        'requiredUppercase': 'required_uppercase',
    }

    api_attributes = [
        'expirationWarning',
        'maxDuration',
        'maxLoginFailures',
        'minDuration',
        'minimumLength',
        'passwordMemory',
        'policyEnforcement',
        'requiredLowercase',
        'requiredNumeric',
        'requiredSpecial',
        'requiredUppercase',
    ]

    returnables = [
        'expiration_warning',
        'max_duration',
        'max_login_failures',
        'min_duration',
        'min_length',
        'password_memory',
        'policy_enforcement',
        'required_lowercase',
        'required_numeric',
        'required_special',
        'required_uppercase',
    ]

    updatables = [
        'expiration_warning',
        'max_duration',
        'max_login_failures',
        'min_duration',
        'min_length',
        'password_memory',
        'policy_enforcement',
        'required_lowercase',
        'required_numeric',
        'required_special',
        'required_uppercase',
    ]

    @property
    def policy_enforcement(self):
        return flatten_boolean(self._values['policy_enforcement'])


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


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
    def policy_enforcement(self):
        if self._values['policy_enforcement'] is None:
            return None
        if self._values['policy_enforcement'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def policy_enforcement(self):
        return flatten_boolean(self._values['policy_enforcement'])


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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
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
        result = dict()

        changed = self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def present(self):
        return self.update()

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
        uri = "https://{0}:{1}/mgmt/tm/auth/password-policy".format(
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
        uri = "https://{0}:{1}/mgmt/tm/auth/password-policy".format(
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
        argument_spec = dict(
            expiration_warning=dict(type='int'),
            max_duration=dict(type='int'),
            max_login_failures=dict(type='int'),
            min_duration=dict(type='int'),
            min_length=dict(type='int'),
            password_memory=dict(type='int'),
            policy_enforcement=dict(type='bool'),
            required_lowercase=dict(type='int'),
            required_numeric=dict(type='int'),
            required_special=dict(type='int'),
            required_uppercase=dict(type='int'),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)


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
