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
module: bigip_provision
short_description: Manage BIG-IP module provisioning.
description:
  - Manage BIG-IP module provisioning. This module will only provision at the
    standard levels of Dedicated, Nominal, and Minimum.
version_added: "2.4"
options:
  module:
    description:
      - The module to provision in BIG-IP.
    required: true
    choices:
      - am
      - afm
      - apm
      - asm
      - avr
      - fps
      - gtm
      - ilx
      - lc
      - ltm
      - pem
      - sam
      - swg
  level:
    description:
      - Sets the provisioning level for the requested modules. Changing the
        level for one module may require modifying the level of another module.
        For example, changing one module to C(dedicated) requires setting all
        others to C(none). Setting the level of a module to C(none) means that
        the module is not run.
    default: nominal
    choices:
      - dedicated
      - nominal
      - minimum
  state:
    description:
      - The state of the provisioned module on the system. When C(present),
        guarantees that the specified module is provisioned at the requested
        level provided that there are sufficient resources on the device (such
        as physical RAM) to support the provisioned module. When C(absent),
        de-provision the module.
    default: present
    choices:
      - present
      - absent
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
requirements:
  - f5-sdk >= 2.2.3
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Provision PEM at "nominal" level
  bigip_provision:
      server: "lb.mydomain.com"
      module: "pem"
      level: "nominal"
      password: "secret"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost

- name: Provision a dedicated SWG. This will unprovision every other module
  bigip_provision:
      server: "lb.mydomain.com"
      module: "swg"
      password: "secret"
      level: "dedicated"
      user: "admin"
      validate_certs: "no"
  delegate_to: localhost
'''

RETURN = '''
level:
    description: The new provisioning level of the module.
    returned: changed
    type: string
    sample: "minimum"
'''

import time

from ansible.module_utils.f5_utils import (
    AnsibleF5Client,
    AnsibleF5Parameters,
    HAS_F5SDK,
    F5ModuleError,
    iControlUnexpectedHTTPError
)


class Parameters(AnsibleF5Parameters):
    api_attributes = ['level']

    returnables = ['level']

    updatables = ['level']

    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
            return result
        except Exception:
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

    @property
    def level(self):
        if self._values['level'] is None:
            return None
        return str(self._values['level'])


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.have = None
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = Parameters(changed)
            return True
        return False

    def exec_module(self):
        if not HAS_F5SDK:
            raise F5ModuleError("The python f5-sdk module is required")

        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.update()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

    def exists(self):
        provision = self.client.api.tm.sys.provision
        resource = getattr(provision, self.want.module)
        resource = resource.load()
        result = resource.attrs
        if str(result['level']) == 'none':
            return False
        return True

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        self.wait_for_module_provisioning()
        return True

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def update_on_device(self):
        params = self.want.api_params()
        provision = self.client.api.tm.sys.provision
        resource = getattr(provision, self.want.module)
        resource = resource.load()
        resource.update(**params)

    def read_current_from_device(self):
        provision = self.client.api.tm.sys.provision
        resource = getattr(provision, str(self.want.module))
        resource = resource.load()
        result = resource.attrs
        return Parameters(result)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        self.wait_for_module_provisioning()
        if self.exists():
            raise F5ModuleError("Failed to de-provision the module")
        return True

    def remove_from_device(self):
        provision = self.client.api.tm.sys.provision
        resource = getattr(provision, self.want.module)
        resource = resource.load()
        resource.update(level='none')

    def wait_for_module_provisioning(self):
        # To prevent things from running forever, the hack is to check
        # for mprov's status twice. If mprov is finished, then in most
        # cases (not ASM) the provisioning is probably ready.
        nops = 0

        # Sleep a little to let provisioning settle and begin properly
        time.sleep(5)

        while nops < 4:
            try:
                if not self._is_mprov_running_on_device():
                    nops += 1
                else:
                    nops = 0
            except Exception:
                # This can be caused by restjavad restarting.
                pass
            time.sleep(10)

    def _is_mprov_running_on_device(self):
        output = self.client.api.tm.util.bash.exec_cmd(
            'run',
            utilCmdArgs='-c "ps aux | grep \'[m]prov\'"'
        )
        if hasattr(output, 'commandResult'):
            return True
        return False


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            module=dict(
                required=True,
                choices=[
                    'afm', 'am', 'sam', 'asm', 'avr', 'fps',
                    'gtm', 'lc', 'ltm', 'pem', 'swg', 'ilx',
                    'apm'
                ]
            ),
            level=dict(
                default='nominal',
                choices=['nominal', 'dedicated', 'minimal']
            ),
            state=dict(
                default='present',
                choices=['present', 'absent']
            )
        )
        self.mutually_exclusive = [
            ['parameters', 'parameters_src']
        ]
        self.f5_product_name = 'bigip'


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        mutually_exclusive=spec.mutually_exclusive,
        supports_check_mode=spec.supports_check_mode,
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
