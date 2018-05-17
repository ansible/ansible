#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_device_group
short_description: Manage device groups on a BIG-IP
description:
  - Managing device groups allows you to create HA pairs and clusters
    of BIG-IP devices. Usage of this module should be done in conjunction
    with the C(bigip_configsync_actions) to sync configuration across
    the pair or cluster if auto-sync is disabled.
version_added: 2.5
options:
  name:
    description:
      - Specifies the name of the device group.
    required: True
  type:
    description:
      - Specifies that the type of group. A C(sync-failover) device group
        contains devices that synchronize their configuration data and fail
        over to one another when a device becomes unavailable. A C(sync-only)
        device group has no such failover. When creating a new device group,
        this option will default to C(sync-only). This setting cannot be
        changed once it has been set.
    choices:
      - sync-failover
      - sync-only
  description:
    description:
      - Description of the device group.
  auto_sync:
    description:
      - Indicates whether configuration synchronization occurs manually or
        automatically. When creating a new device group, this option will
        default to C(false).
    type: bool
  save_on_auto_sync:
    description:
      - When performing an auto-sync, specifies whether the configuration
        will be saved or not. If C(false), only the running configuration
        will be changed on the device(s) being synced to. When creating a
        new device group, this option will default to C(false).
    type: bool
  full_sync:
    description:
      - Specifies whether the system synchronizes the entire configuration
        during synchronization operations. When C(false), the system performs
        incremental synchronization operations, based on the cache size
        specified in C(max_incremental_sync_size). Incremental configuration
        synchronization is a mechanism for synchronizing a device-group's
        configuration among its members, without requiring a full configuration
        load for each configuration change. In order for this to work, all
        devices in the device-group must initially agree on the configuration.
        Typically this requires at least one full configuration load to each
        device. When creating a new device group, this option will default
        to C(false).
    type: bool
  max_incremental_sync_size:
    description:
      - Specifies the size of the changes cache for incremental sync. For example,
        using the default, if you make more than 1024 KB worth of incremental
        changes, the system performs a full synchronization operation. Using
        incremental synchronization operations can reduce the per-device sync/load
        time for configuration changes. This setting is relevant only when
        C(full_sync) is C(false).
  state:
    description:
      - When C(state) is C(present), ensures the device group exists.
      - When C(state) is C(absent), ensures that the device group is removed.
    choices:
      - present
      - absent
    default: present
notes:
  - This module is primarily used as a component of configuring HA pairs of
    BIG-IP devices.
  - Requires BIG-IP >= 12.1.x.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a sync-only device group
  bigip_device_group:
    name: foo-group
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Create a sync-only device group with auto-sync enabled
  bigip_device_group:
    name: foo-group
    auto_sync: yes
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
save_on_auto_sync:
  description: The new save_on_auto_sync value of the device group.
  returned: changed
  type: bool
  sample: true
full_sync:
  description: The new full_sync value of the device group.
  returned: changed
  type: bool
  sample: false
description:
  description: The new description of the device group.
  returned: changed
  type: string
  sample: this is a device group
type:
  description: The new type of the device group.
  returned: changed
  type: string
  sample: sync-failover
auto_sync:
  description: The new auto_sync value of the device group.
  returned: changed
  type: bool
  sample: true
max_incremental_sync_size:
  description: The new sync size of the device group
  returned: changed
  type: int
  sample: 1000
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE

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
        'saveOnAutoSync': 'save_on_auto_sync',
        'fullLoadOnSync': 'full_sync',
        'autoSync': 'auto_sync',
        'incrementalConfigSyncSizeMax': 'max_incremental_sync_size'
    }
    api_attributes = [
        'saveOnAutoSync', 'fullLoadOnSync', 'description', 'type', 'autoSync',
        'incrementalConfigSyncSizeMax'
    ]
    returnables = [
        'save_on_auto_sync', 'full_sync', 'description', 'type', 'auto_sync',
        'max_incremental_sync_size'
    ]
    updatables = [
        'save_on_auto_sync', 'full_sync', 'description', 'auto_sync',
        'max_incremental_sync_size'
    ]

    @property
    def save_on_auto_sync(self):
        if self._values['save_on_auto_sync'] is None:
            return None
        elif self._values['save_on_auto_sync'] in BOOLEANS_TRUE:
            return True
        else:
            return False

    @property
    def auto_sync(self):
        if self._values['auto_sync'] is None:
            return None
        elif self._values['auto_sync'] in [True, 'enabled']:
            return 'enabled'
        else:
            return 'disabled'

    @property
    def full_sync(self):
        if self._values['full_sync'] is None:
            return None
        elif self._values['full_sync'] in BOOLEANS_TRUE:
            return True
        else:
            return False

    @property
    def max_incremental_sync_size(self):
        if not self.full_sync and self._values['max_incremental_sync_size'] is not None:
            if self._values['__warnings'] is None:
                self._values['__warnings'] = []
            self._values['__warnings'].append(
                [
                    dict(
                        msg='"max_incremental_sync_size has no effect if "full_sync" is not true',
                        version='2.4'
                    )
                ]
            )
        if self._values['max_incremental_sync_size'] is None:
            return None
        return int(self._values['max_incremental_sync_size'])

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class Changes(Parameters):
    @property
    def auto_sync(self):
        if self._values['auto_sync'] in BOOLEANS_TRUE:
            return True
        else:
            return False


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = Parameters(params=self.module.params)
        self.have = None
        self.changes = Parameters()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = Changes(params=changed)

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = Changes(params=changed)
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

        changes = self.changes.to_return()
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
        result = self.client.api.tm.cm.device_groups.device_group.exists(
            name=self.want.name
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

    def remove(self):
        if self.module.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the device group")
        return True

    def create(self):
        self._set_changed_options()
        if self.module.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.want.api_params()
        self.client.api.tm.cm.device_groups.device_group.create(
            name=self.want.name,
            **params
        )

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.cm.device_groups.device_group.load(
            name=self.want.name
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.cm.device_groups.device_group.load(
            name=self.want.name
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.cm.device_groups.device_group.load(
            name=self.want.name
        )
        result = resource.attrs
        return Parameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            type=dict(
                choices=['sync-failover', 'sync-only']
            ),
            description=dict(),
            auto_sync=dict(
                type='bool',
                default='no'
            ),
            save_on_auto_sync=dict(
                type='bool',
            ),
            full_sync=dict(
                type='bool'
            ),
            name=dict(
                required=True
            ),
            max_incremental_sync_size=dict(),
            state=dict(
                default='present',
                choices=['absent', 'present']
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
