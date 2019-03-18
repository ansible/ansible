#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_gtm_datacenter
short_description: Manage Datacenter configuration in BIG-IP
description:
  - Manage BIG-IP data center configuration. A data center defines the location
    where the physical network components reside, such as the server and link
    objects that share the same subnet on the network. This module is able to
    manipulate the data center definitions in a BIG-IP.
version_added: 2.2
options:
  contact:
    description:
      - The name of the contact for the data center.
    type: str
  description:
    description:
      - The description of the data center.
    type: str
  location:
    description:
      - The location of the data center.
    type: str
  name:
    description:
      - The name of the data center.
    type: str
    required: True
  state:
    description:
      - The virtual address state. If C(absent), an attempt to delete the
        virtual address will be made. This will only succeed if this
        virtual address is not in use by a virtual server. C(present) creates
        the virtual address and enables it. If C(enabled), enable the virtual
        address if it exists. If C(disabled), create the virtual address if
        needed, and set state to C(disabled).
    type: str
    choices:
      - present
      - absent
      - enabled
      - disabled
    default: present
  partition:
    description:
      - Device partition to manage resources on.
    type: str
    default: Common
    version_added: 2.5
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Create data center "New York"
  bigip_gtm_datacenter:
    name: New York
    location: 222 West 23rd
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
contact:
  description: The contact that was set on the datacenter.
  returned: changed
  type: str
  sample: admin@root.local
description:
  description: The description that was set for the datacenter.
  returned: changed
  type: str
  sample: Datacenter in NYC
enabled:
  description: Whether the datacenter is enabled or not
  returned: changed
  type: bool
  sample: true
disabled:
  description: Whether the datacenter is disabled or not.
  returned: changed
  type: bool
  sample: true
state:
  description: State of the datacenter.
  returned: changed
  type: str
  sample: disabled
location:
  description: The location that is set for the datacenter.
  returned: changed
  type: str
  sample: 222 West 23rd
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import transform_name
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import transform_name
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    api_map = {}

    updatables = [
        'location', 'description', 'contact', 'state',
    ]

    returnables = [
        'location', 'description', 'contact', 'state', 'enabled', 'disabled',
    ]

    api_attributes = [
        'enabled', 'location', 'description', 'contact', 'disabled',
    ]


class ApiParameters(Parameters):
    @property
    def disabled(self):
        if self._values['disabled'] is True:
            return True
        return None

    @property
    def enabled(self):
        if self._values['enabled'] is True:
            return True
        return None


class ModuleParameters(Parameters):
    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True
        return None

    @property
    def enabled(self):
        if self._values['state'] in ['enabled', 'present']:
            return True
        return None

    @property
    def state(self):
        if self.enabled and self._values['state'] != 'present':
            return 'enabled'
        elif self.disabled and self._values['state'] != 'present':
            return 'disabled'
        else:
            return self._values['state']


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
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True

    @property
    def enabled(self):
        if self._values['state'] in ['enabled', 'present']:
            return True


class ReportableChanges(Changes):
    @property
    def disabled(self):
        if self._values['state'] == 'disabled':
            return True
        elif self._values['state'] in ['enabled', 'present']:
            return False
        return None

    @property
    def enabled(self):
        if self._values['state'] in ['enabled', 'present']:
            return True
        elif self._values['state'] == 'disabled':
            return False
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

    @property
    def state(self):
        if self.want.enabled != self.have.enabled:
            return dict(
                state=self.want.state,
                enabled=self.want.enabled
            )
        if self.want.disabled != self.have.disabled:
            return dict(
                state=self.want.state,
                disabled=self.want.disabled
            )


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
            self.changes = UsableChanges(params=changed)
            return True
        return False

    def exec_module(self):
        if not module_provisioned(self.client, 'gtm'):
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
        changed = False
        result = dict()
        state = self.want.state

        if state in ['present', 'enabled', 'disabled']:
            changed = self.present()
        elif state == "absent":
            changed = self.absent()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

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

    def create(self):
        self.have = ApiParameters()
        self.should_update()
        if self.module.check_mode:
            return True
        self.create_on_device()
        if self.exists():
            return True
        else:
            raise F5ModuleError("Failed to create the datacenter")

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

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the datacenter")
        return True

    def exists(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/datacenter/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.get(uri)
        try:
            response = resp.json()
        except ValueError:
            return False
        if resp.status == 404 or 'code' in response and response['code'] == 404:
            return False
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        params['name'] = self.want.name
        params['partition'] = self.want.partition
        uri = "https://{0}:{1}/mgmt/tm/gtm/datacenter/".format(
            self.client.provider['server'],
            self.client.provider['server_port']
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/gtm/datacenter/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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

    def remove_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/datacenter/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
        )
        resp = self.client.api.delete(uri)
        if resp.status == 200:
            return True

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/gtm/datacenter/{2}".format(
            self.client.provider['server'],
            self.client.provider['server_port'],
            transform_name(self.want.partition, self.want.name)
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
            contact=dict(),
            description=dict(),
            location=dict(),
            name=dict(required=True),
            state=dict(
                default='present',
                choices=['present', 'absent', 'disabled', 'enabled']
            ),
            partition=dict(
                default='Common',
                fallback=(env_fallback, ['F5_PARTITION'])
            )
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
