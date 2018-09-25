#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

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
  description:
    description:
      - The description of the data center.
  location:
    description:
      - The location of the data center.
  name:
    description:
      - The name of the data center.
    required: True
  state:
    description:
      - The virtual address state. If C(absent), an attempt to delete the
        virtual address will be made. This will only succeed if this
        virtual address is not in use by a virtual server. C(present) creates
        the virtual address and enables it. If C(enabled), enable the virtual
        address if it exists. If C(disabled), create the virtual address if
        needed, and set state to C(disabled).
    default: present
    choices:
      - present
      - absent
      - enabled
      - disabled
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create data center "New York"
  bigip_gtm_datacenter:
    server: lb.mydomain.com
    user: admin
    password: secret
    name: New York
    location: 222 West 23rd
  delegate_to: localhost
'''

RETURN = r'''
contact:
  description: The contact that was set on the datacenter.
  returned: changed
  type: string
  sample: admin@root.local
description:
  description: The description that was set for the datacenter.
  returned: changed
  type: string
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
  type: string
  sample: disabled
location:
  description: The location that is set for the datacenter.
  returned: changed
  type: string
  sample: 222 West 23rd
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

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
    api_map = {}

    updatables = [
        'location', 'description', 'contact', 'state'
    ]

    returnables = [
        'location', 'description', 'contact', 'state', 'enabled', 'disabled'
    ]

    api_attributes = [
        'enabled', 'location', 'description', 'contact', 'disabled'
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
            if api_attribute in self.api_map:
                result[api_attribute] = getattr(
                    self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


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
        else:
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
    pass


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
        self.client = kwargs.pop('client', None)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state in ['present', 'enabled', 'disabled']:
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
        resource = self.client.api.tm.gtm.datacenters.datacenter.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(params=result)

    def exists(self):
        result = self.client.api.tm.gtm.datacenters.datacenter.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.module.check_mode:
            return True
        self.update_on_device()
        return True

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.gtm.datacenters.datacenter.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

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

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.gtm.datacenters.datacenter.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the datacenter")
        return True

    def remove_from_device(self):
        resource = self.client.api.tm.gtm.datacenters.datacenter.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.delete()


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
