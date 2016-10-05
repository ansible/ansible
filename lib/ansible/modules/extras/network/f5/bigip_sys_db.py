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
module: bigip_sys_db
short_description: Manage BIG-IP system database variables
description:
  - Manage BIG-IP system database variables
version_added: "2.2"
options:
  key:
    description:
      - The database variable to manipulate.
    required: true
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value). When C(reset) sets the
        variable back to the default value. At least one of value and state
        C(reset) are required.
    required: false
    default: present
    choices:
      - present
      - reset
  value:
    description:
      - The value to set the key to. At least one of value and state C(reset)
        are required.
    required: false
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Set the boot.quiet DB variable on the BIG-IP
  bigip_sys_db:
      user: "admin"
      password: "secret"
      server: "lb.mydomain.com"
      key: "boot.quiet"
      value: "disable"
  delegate_to: localhost

- name: Disable the initial setup screen
  bigip_sys_db:
      user: "admin"
      password: "secret"
      server: "lb.mydomain.com"
      key: "setup.run"
      value: "false"
  delegate_to: localhost

- name: Reset the initial setup screen
  bigip_sys_db:
      user: "admin"
      password: "secret"
      server: "lb.mydomain.com"
      key: "setup.run"
      state: "reset"
  delegate_to: localhost
'''

RETURN = '''
name:
    description: The key in the system database that was specified
    returned: changed and success
    type: string
    sample: "setup.run"
default_value:
    description: The default value of the key
    returned: changed and success
    type: string
    sample: "true"
value:
    description: The value that you set the key to
    returned: changed and success
    type: string
    sample: "false"
'''

try:
    from f5.bigip import ManagementRoot
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


class BigIpSysDb(object):
    def __init__(self, *args, **kwargs):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        self.params = kwargs
        self.api = ManagementRoot(kwargs['server'],
                                  kwargs['user'],
                                  kwargs['password'],
                                  port=kwargs['server_port'])

    def flush(self):
        result = dict()
        state = self.params['state']
        value = self.params['value']

        if not state == 'reset' and not value:
            raise F5ModuleError(
                "When setting a key, a value must be supplied"
            )

        current = self.read()

        if self.params['check_mode']:
            if value == current:
                changed = False
            else:
                changed = True
        else:
            if state == "present":
                changed = self.present()
            elif state == "reset":
                changed = self.reset()
            current = self.read()
            result.update(
                name=current.name,
                default_value=current.defaultValue,
                value=current.value
            )

        result.update(dict(changed=changed))
        return result

    def read(self):
        dbs = self.api.tm.sys.dbs.db.load(
            name=self.params['key']
        )
        return dbs

    def present(self):
        current = self.read()

        if current.value == self.params['value']:
            return False

        current.update(value=self.params['value'])
        current.refresh()

        if current.value != self.params['value']:
            raise F5ModuleError(
                "Failed to set the DB variable"
            )
        return True

    def reset(self):
        current = self.read()

        default = current.defaultValue
        if current.value == default:
            return False

        current.update(value=default)
        current.refresh()

        if current.value != current.defaultValue:
            raise F5ModuleError(
                "Failed to reset the DB variable"
            )

        return True


def main():
    argument_spec = f5_argument_spec()

    meta_args = dict(
        key=dict(required=True),
        state=dict(default='present', choices=['present', 'reset']),
        value=dict(required=False, default=None)
    )
    argument_spec.update(meta_args)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    try:
        obj = BigIpSysDb(check_mode=module.check_mode, **module.params)
        result = obj.flush()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
