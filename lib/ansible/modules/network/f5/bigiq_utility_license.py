#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigiq_utility_license
short_description: Manage utility licenses on a BIG-IQ
description:
  - Manages utility licenses on a BIG-IQ. Utility licenses are one form of licenses
    that BIG-IQ can distribute. These licenses, unlike regkey licenses, do not require
    a pool to be created before creation. Additionally, when assigning them, you assign
    by offering instead of key.
version_added: 2.6
options:
  license_key:
    description:
      - The license key to install and activate.
    required: True
  accept_eula:
    description:
      - A key that signifies that you accept the F5 EULA for this license.
      - A copy of the EULA can be found here https://askf5.f5.com/csp/article/K12902
      - This is required when C(state) is C(present).
    type: bool
  state:
    description:
      - The state of the utility license on the system.
      - When C(present), guarantees that the license exists.
      - When C(absent), removes the license from the system.
    default: present
    choices:
      - absent
      - present
requirements:
  - BIG-IQ >= 5.3.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add a utility license to the system
  bigiq_utility_license:
    license_key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    accept_eula: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove a utility license from the system
  bigiq_utility_license:
    license_key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import time

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigiq import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import exit_json
    from library.module_utils.network.f5.common import fail_json
except ImportError:
    from ansible.module_utils.network.f5.bigiq import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import exit_json
    from ansible.module_utils.network.f5.common import fail_json


class Parameters(AnsibleF5Parameters):
    api_map = {
        'regKey': 'license_key'
    }

    api_attributes = [
        'regKey'
    ]

    returnables = [
        'license_key'
    ]

    updatables = [
        'license_key'
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
    pass


class ReportableChanges(Changes):
    @property
    def license_key(self):
        return None


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
        self.client = kwargs.get('client', None)
        self.want = ModuleParameters(client=self.client, params=self.module.params)
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

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        if state == "present":
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
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
            return False
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/utility/licenses/?$filter=regKey+eq+'{2}'".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.license_key
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if resp.status == 200 and response['totalItems'] == 0:
            return False
        elif 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        self.wait_for_removal()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        if self.want.accept_eula is False:
            raise F5ModuleError(
                "To add a license, you must accept its EULA. Please see the module documentation for a link to this."
            )
        self.create_on_device()
        self.wait_for_initial_license_activation()
        self.wait_for_utility_license_activation()
        if not self.exists():
            raise F5ModuleError(
                "Failed to activate the license."
            )
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/initial-activation'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
        )

        params['name'] = self.want.license_key
        params['status'] = 'ACTIVATING_AUTOMATIC'

        resp = self.client.api.post(uri, json=params)
        try:
            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)

    def wait_for_removal(self):
        count = 0

        while count < 3:
            if not self.exists():
                count += 1
            else:
                count = 0
            time.sleep(1)

    def wait_for_initial_license_activation(self):
        count = 0
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/initial-activation/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.license_key
        )

        while count < 3:
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] == 400:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp._content)

            if response['status'] == 'READY':
                count += 1
            elif response['status'] == 'ACTIVATING_AUTOMATIC_NEED_EULA_ACCEPT':
                uri = response['selfLink'].replace(
                    'https://localhost',
                    'https://{0}:{1}'.format(
                        self.client.provider['server'],
                        self.client.provider['server_port']
                    )
                )
                self.client.api.patch(uri, json=dict(
                    status='ACTIVATING_AUTOMATIC_EULA_ACCEPTED',
                    eulaText=response['eulaText']
                ))
            elif response['status'] == 'ACTIVATION_FAILED':
                raise F5ModuleError(str(response['message']))
            else:
                count = 0
            time.sleep(1)

    def wait_for_utility_license_activation(self):
        count = 0
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/utility/licenses/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.license_key
        )

        while count < 3:
            resp = self.client.api.get(uri)
            try:
                response = resp.json()
            except ValueError as ex:
                raise F5ModuleError(str(ex))

            if 'code' in response and response['code'] in [400, 401]:
                if 'message' in response:
                    raise F5ModuleError(response['message'])
                else:
                    raise F5ModuleError(resp._content)

            if response['status'] == 'READY':
                count += 1
            elif response['status'] == 'ACTIVATION_FAILED':
                raise F5ModuleError(str(response['message']))
            else:
                count = 0
            time.sleep(1)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = 'https://{0}:{1}/mgmt/cm/device/licensing/pool/utility/licenses/{2}'.format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.license_key
        )

        resp = self.client.api.delete(uri)
        try:

            response = resp.json()
        except ValueError as ex:
            raise F5ModuleError(str(ex))

        if 'code' in response and response['code'] == 400:
            if 'message' in response:
                raise F5ModuleError(response['message'])
            else:
                raise F5ModuleError(resp._content)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            license_key=dict(required=True, no_log=True),
            accept_eula=dict(type='bool'),
            state=dict(
                default='present',
                choices=['present', 'absent']
            ),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)
        self.required_if = [
            ['state', 'present', ['accept_eula']]
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        required_if=spec.required_if
    )

    try:
        client = F5RestClient(module=module)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        exit_json(module, results, client)
    except F5ModuleError as ex:
        fail_json(module, ex, client)


if __name__ == '__main__':
    main()
