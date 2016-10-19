#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
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

DOCUMENTATION = '''
---
module: bigip_hostname
short_description: Manage the hostname of a BIG-IP.
description:
  - Manage the hostname of a BIG-IP.
version_added: "2.3"
options:
  hostname:
    description:
      - Hostname of the BIG-IP host.
    required: true
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Set the hostname of the BIG-IP
  bigip_hostname:
      hostname: "bigip.localhost.localdomain"
      password: "admin"
      server: "bigip.localhost.localdomain"
      user: "admin"
  delegate_to: localhost
'''

RETURN = '''
hostname:
    description: The new hostname of the device
    returned: changed
    type: string
    sample: "big-ip01.internal"
'''

try:
    from f5.bigip.contexts import TransactionContextManager
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


class BigIpHostnameManager(object):
    def __init__(self, *args, **kwargs):
        self.changed_params = dict()
        self.params = kwargs
        self.api = None

    def connect_to_bigip(self, **kwargs):
        return ManagementRoot(kwargs['server'],
                              kwargs['user'],
                              kwargs['password'],
                              port=kwargs['server_port'])

    def ensure_hostname_is_present(self):
        self.changed_params['hostname'] = self.params['hostname']

        if self.params['check_mode']:
            return True

        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            r = api.tm.sys.global_settings.load()
            r.update(hostname=self.params['hostname'])

        if self.hostname_exists():
            return True
        else:
            raise F5ModuleError("Failed to set the hostname")

    def hostname_exists(self):
        if self.params['hostname'] == self.current_hostname():
            return True
        else:
            return False

    def present(self):
        if self.hostname_exists():
            return False
        else:

            return self.ensure_hostname_is_present()

    def current_hostname(self):
        r = self.api.tm.sys.global_settings.load()
        return r.hostname

    def apply_changes(self):
        result = dict()

        changed = self.apply_to_running_config()
        if changed:
            self.save_running_config()

        result.update(**self.changed_params)
        result.update(dict(changed=changed))
        return result

    def apply_to_running_config(self):
        try:
            self.api = self.connect_to_bigip(**self.params)
            return self.present()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

    def save_running_config(self):
        self.api.tm.sys.config.exec_cmd('save')


class BigIpHostnameModuleConfig(object):
    def __init__(self):
        self.argument_spec = dict()
        self.meta_args = dict()
        self.supports_check_mode = True

        self.initialize_meta_args()
        self.initialize_argument_spec()

    def initialize_meta_args(self):
        args = dict(
            hostname=dict(required=True)
        )
        self.meta_args = args

    def initialize_argument_spec(self):
        self.argument_spec = f5_argument_spec()
        self.argument_spec.update(self.meta_args)

    def create(self):
        return AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=self.supports_check_mode
        )


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    config = BigIpHostnameModuleConfig()
    module = config.create()

    try:
        obj = BigIpHostnameManager(
            check_mode=module.check_mode, **module.params
        )
        result = obj.apply_changes()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
