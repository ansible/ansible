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
module: bigip_configsync_action
short_description: Perform different actions related to config-sync
description:
  - Allows one to run different config-sync actions. These actions allow
    you to manually sync your configuration across multiple BIG-IPs when
    those devices are in an HA pair.
version_added: 2.4
options:
  device_group:
    description:
      - The device group that you want to perform config-sync actions on.
    required: True
  sync_device_to_group:
    description:
      - Specifies that the system synchronizes configuration data from this
        device to other members of the device group. In this case, the device
        will do a "push" to all the other devices in the group. This option
        is mutually exclusive with the C(sync_group_to_device) option.
    type: bool
  sync_most_recent_to_device:
    description:
      - Specifies that the system synchronizes configuration data from the
        device with the most recent configuration. In this case, the device
        will do a "pull" from the most recently updated device. This option
        is mutually exclusive with the C(sync_device_to_group) options.
    type: bool
  overwrite_config:
    description:
      - Indicates that the sync operation overwrites the configuration on
        the target.
    default: no
    type: bool
notes:
  - Requires the objectpath Python package on the host. This is as easy as
    C(pip install objectpath).
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Sync configuration from device to group
  bigip_configsync_action:
    device_group: foo-group
    sync_device_to_group: yes
    server: lb.mydomain.com
    user: admin
    password: secret
    validate_certs: no
  delegate_to: localhost

- name: Sync configuration from most recent device to the current host
  bigip_configsync_action:
    device_group: foo-group
    sync_most_recent_to_device: yes
    server: lb.mydomain.com
    user: admin
    password: secret
    validate_certs: no
  delegate_to: localhost

- name: Perform an initial sync of a device to a new device group
  bigip_configsync_action:
    device_group: new-device-group
    sync_device_to_group: yes
    server: lb.mydomain.com
    user: admin
    password: secret
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
# only common fields returned
'''

import re
import time

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

try:
    from objectpath import Tree
    HAS_OBJPATH = True
except ImportError:
    HAS_OBJPATH = False


class Parameters(AnsibleF5Parameters):
    api_attributes = []
    returnables = []

    @property
    def direction(self):
        if self.sync_device_to_group:
            return 'to-group'
        else:
            return 'from-group'

    @property
    def sync_device_to_group(self):
        result = self._cast_to_bool(self._values['sync_device_to_group'])
        return result

    @property
    def sync_group_to_device(self):
        result = self._cast_to_bool(self._values['sync_group_to_device'])
        return result

    @property
    def force_full_push(self):
        if self.overwrite_config:
            return 'force-full-load-push'
        else:
            return ''

    @property
    def overwrite_config(self):
        result = self._cast_to_bool(self._values['overwrite_config'])
        return result

    def _cast_to_bool(self, value):
        if value is None:
            return None
        elif value in BOOLEANS_TRUE:
            return True
        else:
            return False

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.want = Parameters(params=self.module.params)
        self.changes = Parameters()

    def exec_module(self):
        result = dict()

        try:
            changed = self.present()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(dict(changed=changed))
        return result

    def present(self):
        if not self._device_group_exists():
            raise F5ModuleError(
                "The specified 'device_group' not not exist."
            )
        if self._sync_to_group_required():
            raise F5ModuleError(
                "This device group needs an initial sync. Please use "
                "'sync_device_to_group'"
            )
        if self.exists():
            return False
        else:
            return self.execute()

    def _sync_to_group_required(self):
        resource = self.read_current_from_device()
        status = self._get_status_from_resource(resource)
        if status == 'Awaiting Initial Sync' and self.want.sync_group_to_device:
            return True
        return False

    def _device_group_exists(self):
        result = self.client.api.tm.cm.device_groups.device_group.exists(
            name=self.want.device_group
        )
        return result

    def execute(self):
        self.execute_on_device()
        self._wait_for_sync()
        return True

    def exists(self):
        resource = self.read_current_from_device()
        status = self._get_status_from_resource(resource)
        if status == 'In Sync':
            return True
        else:
            return False

    def execute_on_device(self):
        sync_cmd = 'config-sync {0} {1} {2}'.format(
            self.want.direction,
            self.want.device_group,
            self.want.force_full_push
        )
        self.client.api.tm.cm.exec_cmd(
            'run',
            utilCmdArgs=sync_cmd
        )

    def _wait_for_sync(self):
        # Wait no more than half an hour
        resource = self.read_current_from_device()
        for x in range(1, 180):
            time.sleep(3)
            status = self._get_status_from_resource(resource)

            # Changes Pending:
            #     The existing device has changes made to it that
            #     need to be sync'd to the group.
            #
            # Awaiting Initial Sync:
            #     This is a new device group and has not had any sync
            #     done yet. You _must_ `sync_device_to_group` in this
            #     case.
            #
            # Not All Devices Synced:
            #     A device group will go into this state immediately
            #     after starting the sync and stay until all devices finish.
            #
            if status in ['Changes Pending']:
                details = self._get_details_from_resource(resource)
                self._validate_pending_status(details)
            elif status in ['Awaiting Initial Sync', 'Not All Devices Synced']:
                pass
            elif status == 'In Sync':
                return
            else:
                raise F5ModuleError(status)

    def read_current_from_device(self):
        result = self.client.api.tm.cm.sync_status.load()
        return result

    def _get_status_from_resource(self, resource):
        resource.refresh()
        entries = resource.entries.copy()
        k, v = entries.popitem()
        status = v['nestedStats']['entries']['status']['description']
        return status

    def _get_details_from_resource(self, resource):
        resource.refresh()
        stats = resource.entries.copy()
        tree = Tree(stats)
        details = list(tree.execute('$..*["details"]["description"]'))
        result = details[::-1]
        return result

    def _validate_pending_status(self, details):
        """Validate the content of a pending sync operation

        This is a hack. The REST API is not consistent with its 'status' values
        so this method is here to check the returned strings from the operation
        and see if it reported any of these inconsistencies.

        :param details:
        :raises F5ModuleError:
        """
        pattern1 = r'.*(?P<msg>Recommended\s+action.*)'
        for detail in details:
            matches = re.search(pattern1, detail)
            if matches:
                raise F5ModuleError(matches.group('msg'))


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = False

        argument_spec = dict(
            sync_device_to_group=dict(
                type='bool'
            ),
            sync_most_recent_to_device=dict(
                type='bool'
            ),
            overwrite_config=dict(
                type='bool',
                default='no'
            ),
            device_group=dict(
                required=True
            )
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_argument_spec)
        self.argument_spec.update(argument_spec)

        self.required_one_of = [
            ['sync_device_to_group', 'sync_most_recent_to_device']
        ]
        self.mutually_exclusive = [
            ['sync_device_to_group', 'sync_most_recent_to_device']
        ]
        self.required_one_of = [
            ['sync_device_to_group', 'sync_most_recent_to_device']
        ]


def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
        required_one_of=spec.required_one_of
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
