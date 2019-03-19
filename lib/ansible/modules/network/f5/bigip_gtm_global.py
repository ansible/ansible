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
module: bigip_gtm_global
short_description: Manages global GTM settings
description:
  - Manages global GTM settings. These settings include general, load balancing, and metrics
    related settings.
version_added: 2.6
options:
  synchronization:
    description:
      - Specifies whether this system is a member of a synchronization group.
      - When you enable synchronization, the system periodically queries other systems in
        the synchronization group to obtain and distribute configuration and metrics collection
        updates.
      - The synchronization group may contain systems configured as Global Traffic Manager and
        Link Controller systems.
    type: bool
  synchronization_group_name:
    description:
      - Specifies the name of the synchronization group to which the system belongs.
    type: str
  synchronize_zone_files:
    description:
      - Specifies that the system synchronizes Domain Name System (DNS) zone files among the
        synchronization group members.
    type: bool
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Configure synchronization settings
  bigip_gtm_global:
    synchronization: yes
    synchronization_group_name: my-group
    synchronize_zone_files: yes
    state: present
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
synchronization:
  description: The synchronization setting on the system.
  returned: changed
  type: bool
  sample: true
synchronization_group_name:
  description: The synchronization group name.
  returned: changed
  type: str
  sample: my-group
synchronize_zone_files:
  description: Whether or not the system will sync zone files.
  returned: changed
  type: str
  sample: my-group
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.icontrol import module_provisioned
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.icontrol import module_provisioned


class Parameters(AnsibleF5Parameters):
    api_map = {
        'synchronizationGroupName': 'synchronization_group_name',
        'synchronizeZoneFiles': 'synchronize_zone_files',
    }

    api_attributes = [
        'synchronizeZoneFiles', 'synchronizationGroupName', 'synchronization',
    ]

    returnables = [
        'synchronization', 'synchronization_group_name', 'synchronize_zone_files',
    ]

    updatables = [
        'synchronization', 'synchronization_group_name', 'synchronize_zone_files',
    ]


class ApiParameters(Parameters):
    @property
    def synchronization(self):
        if self._values['synchronization'] is None:
            return None
        elif self._values['synchronization'] == 'no':
            return False
        else:
            return True

    @property
    def synchronize_zone_files(self):
        if self._values['synchronize_zone_files'] is None:
            return None
        elif self._values['synchronize_zone_files'] == 'no':
            return False
        else:
            return True

    @property
    def synchronization_group_name(self):
        if self._values['synchronization_group_name'] is None:
            return None
        return str(self._values['synchronization_group_name'])


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
    def synchronization(self):
        if self._values['synchronization'] is None:
            return None
        elif self._values['synchronization'] is False:
            return 'no'
        else:
            return 'yes'

    @property
    def synchronize_zone_files(self):
        if self._values['synchronize_zone_files'] is None:
            return None
        elif self._values['synchronize_zone_files'] is False:
            return 'no'
        else:
            return 'yes'


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
    def synchronization_group_name(self):
        if self.want.synchronization_group_name is None:
            return None
        if self.want.synchronization_group_name == '' and self.have.synchronization_group_name is None:
            return None
        if self.want.synchronization_group_name != self.have.synchronization_group_name:
            return self.want.synchronization_group_name


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

    def exec_module(self):  # lgtm [py/similar-function]
        if not module_provisioned(self.client, 'gtm'):
            raise F5ModuleError(
                "GTM must be provisioned to use this module."
            )
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

    def update(self):
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
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/gtm/global-settings/general/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/gtm/global-settings/general/".format(
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
            synchronization=dict(type='bool'),
            synchronization_group_name=dict(),
            synchronize_zone_files=dict(type='bool')
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
