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
    required: True
  license_key:
    description:
      - The license key to put in the pool.
    required: True
  description:
    description:
      - Description of the license.
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
- name: Add a registration key license to a pool
  bigiq_regkey_license:
    regkey_pool: foo-pool
    license_key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    accept_eula: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove a registration key license from a pool
  bigiq_regkey_license:
    regkey_pool: foo-pool
    license_key: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
description:
  description: The new description of the license key.
  returned: changed
  type: string
  sample: My license for BIG-IP 1
'''

import time

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigiq import HAS_F5SDK
    from library.module_utils.network.f5.bigiq import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
except ImportError:
    from ansible.module_utils.network.f5.bigiq import HAS_F5SDK
    from ansible.module_utils.network.f5.bigiq import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


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
        collection = self.client.api.cm.device.licensing.pool.regkey.licenses_s.get_collection()
        resource = next((x for x in collection if x.name == self.regkey_pool), None)
        if resource is None:
            raise F5ModuleError("Could not find the specified regkey pool.")
        self._values['regkey_pool_uuid'] = resource.id
        return resource.id


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

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

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
        collection = self.client.api.cm.device.licensing.pool.regkey.licenses_s
        pool = collection.licenses.load(id=self.want.regkey_pool_uuid)
        collection = pool.offerings_s.get_collection()
        resource = next((x for x in collection if x.regKey == self.want.license_key), None)
        if resource is None:
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
        collection = self.client.api.cm.device.licensing.pool.regkey.licenses_s
        pool = collection.licenses.load(id=self.want.regkey_pool_uuid)
        resource = pool.offerings_s.offerings.create(
            status='ACTIVATING_AUTOMATIC',
            **params
        )
        for x in range(60):
            resource.refresh()
            if resource.status == 'READY':
                break
            elif resource.status == 'ACTIVATING_AUTOMATIC_NEED_EULA_ACCEPT':
                resource.modify(
                    status='ACTIVATING_AUTOMATIC_EULA_ACCEPTED',
                    eulaText=resource.eulaText
                )
            elif resource.status == 'ACTIVATION_FAILED':
                raise F5ModuleError(str(resource.message))
            time.sleep(1)

    def wait_for_status(self, resource, status):
        for x in range(60):
            resource.refresh()
            if resource.status == status:
                return
            time.sleep(1)

    def update_on_device(self):
        params = self.changes.api_params()
        collection = self.client.api.cm.device.licensing.pool.regkey.licenses_s
        pool = collection.licenses.load(id=self.want.regkey_pool_uuid)
        collection = pool.offerings_s.get_collection()
        resource = next((x for x in collection if x.regKey == self.want.license_key), None)
        if resource is None:
            return False
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        collection = self.client.api.cm.device.licensing.pool.regkey.licenses_s
        pool = collection.licenses.load(id=self.want.regkey_pool_uuid)
        collection = pool.offerings_s.get_collection()
        resource = next((x for x in collection if x.regKey == self.want.license_key), None)
        if resource is None:
            return False
        if resource:
            resource.delete()

    def read_current_from_device(self):
        collection = self.client.api.cm.device.licensing.pool.regkey.licenses_s
        pool = collection.licenses.load(id=self.want.regkey_pool_uuid)
        collection = pool.offerings_s.get_collection()
        resource = next((x for x in collection if x.regKey == self.want.license_key), None)
        if resource is None:
            return False
        result = resource.attrs
        return ApiParameters(params=result)


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
        required_if=spec.required_if
    )
    if not HAS_F5SDK:
        module.fail_json(msg="The python f5-sdk module is required")

    try:
        client = F5Client(**module.params)
        mm = ModuleManager(module=module, client=client)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
