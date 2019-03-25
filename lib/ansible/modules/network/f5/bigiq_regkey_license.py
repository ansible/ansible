#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigiq_regkey_license
short_description: Manages licenses in a BIG-IQ registration key pool
description:
  - Manages licenses in a BIG-IQ registration key pool.
version_added: 2.5
options:
  regkey_pool:
    description:
      - The registration key pool that you want to place the license in.
      - You must be mindful to name your registration pools unique names. While
        BIG-IQ does not require this, this module does. If you do not do this,
        the behavior of the module is undefined and you may end up putting
        licenses in the wrong registration key pool.
    type: str
    required: True
  license_key:
    description:
      - The license key to put in the pool.
    type: str
    required: True
  description:
    description:
      - Description of the license.
    type: str
  accept_eula:
    description:
      - A key that signifies that you accept the F5 EULA for this license.
      - A copy of the EULA can be found here https://askf5.f5.com/csp/article/K12902
      - This is required when C(state) is C(present).
    type: bool
  state:
    description:
      - The state of the regkey license in the pool on the system.
      - When C(present), guarantees that the license exists in the pool.
      - When C(absent), removes the license from the pool.
    type: str
    choices:
      - absent
      - present
    default: present
requirements:
  - BIG-IQ >= 5.3.0
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Add a registration key license to a pool
  bigiq_regkey_license:
    regkey_pool: foo-pool
    license_key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    accept_eula: yes
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Remove a registration key license from a pool
  bigiq_regkey_license:
    regkey_pool: foo-pool
    license_key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    state: absent
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the license key.
  returned: changed
  type: str
  sample: My license for BIG-IP 1
'''

import time

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigiq import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigiq import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec


class Parameters(AnsibleF5Parameters):
    api_map = {
        'regKey': 'license_key'
    }

    api_attributes = [
        'regKey', 'description'
    ]

    returnables = [
        'description'
    ]

    updatables = [
        'description'
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
    @property
    def regkey_pool_uuid(self):
        if self._values['regkey_pool_uuid']:
            return self._values['regkey_pool_uuid']
        collection = self.read_current_from_device()
        resource = next((x for x in collection if x.name == self.regkey_pool), None)
        if resource is None:
            raise F5ModuleError("Could not find the specified regkey pool.")
        self._values['regkey_pool_uuid'] = resource.id
        return resource.id

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses".format(
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
        if 'items' not in response:
            return []
        result = [ApiParameters(params=r) for r in response['items']]
        return result


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


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
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
            return self.update()
        else:
            return self.create()

    def exists(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.regkey_pool_uuid,
            self.want.license_key
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
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
        return True

    def create_on_device(self):
        params = self.want.api_params()
        params['name'] = self.want.name
        params['status'] = 'ACTIVATING_AUTOMATIC'
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.regkey_pool_uuid,
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

        for x in range(60):
            resource = self.read_current_from_device()
            if resource.status == 'READY':
                break
            elif resource.status == 'ACTIVATING_AUTOMATIC_NEED_EULA_ACCEPT':
                params = dict(
                    status='ACTIVATING_AUTOMATIC_EULA_ACCEPTED',
                    eulaText=resource.eulaText
                )
                uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}".format(
                    self.client.provider['server'],
                    self.client.provider['server_port'],
                    self.want.regkey_pool_uuid,
                    self.want.license_key
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
            elif resource.status == 'ACTIVATION_FAILED':
                raise F5ModuleError(str(resource.message))
            time.sleep(1)

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.regkey_pool_uuid,
            self.want.license_key
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

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.regkey_pool_uuid,
            self.want.license_key
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/cm/device/licensing/pool/regkey/licenses/{2}/offerings/{3}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            self.want.regkey_pool_uuid,
            self.want.license_key
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
            regkey_pool=dict(required=True),
            license_key=dict(required=True, no_log=True),
            description=dict(),
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
        required_if=spec.required_if,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
