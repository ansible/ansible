#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bigip_configsync_actions
short_description: Perform different actions related to config-sync.
description:
  - Allows one to run different config-sync actions. These actions allow
    you to manually sync your configuration across multiple BIG-IPs when
    those devices are in an HA pair.
version_added: "2.4"
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
    choices:
      - yes
      - no
  sync_most_recent_to_device:
    description:
      - Specifies that the system synchronizes configuration data from the
        device with the most recent configuration. In this case, the device
        will do a "pull" from the most recently updated device. This option
        is mutually exclusive with the C(sync_device_to_group) options.
    choices:
      - yes
      - no
  overwrite_config:
    description:
      - Indicates that the sync operation overwrites the configuration on
        the target.
    default: no
    choices:
      - yes
      - no
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires the objectpath Python package on the host. This is as easy as pip
    install objectpath.
requirements:
  - f5-sdk >= 2.2.3
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Sync configuration from device to group
  bigip_configsync_actions:
      device_group: "foo-group"
      sync_device_to_group: yes
      server: "lb01.mydomain.com"
      user: "admin"
      password: "secret"
      validate_certs: no
  delegate_to: localhost

- name: Sync configuration from most recent device to the current host
  bigip_configsync_actions:
      device_group: "foo-group"
      sync_most_recent_to_device: yes
      server: "lb01.mydomain.com"
      user: "admin"
      password: "secret"
      validate_certs: no
  delegate_to: localhost

- name: Perform an initial sync of a device to a new device group
  bigip_configsync_actions:
      device_group: "new-device-group"
      sync_device_to_group: yes
      server: "lb01.mydomain.com"
      user: "admin"
      password: "secret"
      validate_certs: no
  delegate_to: localhost
'''

RETURN = '''
# only common fields returned
'''

import time
import re

try:
    from objectpath import Tree
    HAS_OBJPATH = True
except ImportError:
    HAS_OBJPATH = False

from ansible.module_utils.basic import BOOLEANS_TRUE
from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)


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
    def __init__(self, client):
        self.client = client
        self.want = Parameters(self.client.module.params)

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
                pass
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
        self.supports_check_mode = True
        self.argument_spec = dict(
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
        self.f5_product_name = 'bigip'
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
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    if not HAS_OBJPATH:
        raise F5ModuleError("The python objectpath module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        mutually_exclusive=spec.mutually_exclusive,
        required_one_of=spec.required_one_of,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        client.module.exit_json(**results)
    except F5ModuleError as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
