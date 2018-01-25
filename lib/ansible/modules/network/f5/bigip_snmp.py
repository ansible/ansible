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
module: bigip_snmp
short_description: Manipulate general SNMP settings on a BIG-IP
description:
  - Manipulate general SNMP settings on a BIG-IP.
version_added: 2.4
options:
  contact:
    description:
      - Specifies the name of the person who administers the SNMP
        service for this system.
  agent_status_traps:
    description:
      - When C(enabled), ensures that the system sends a trap whenever the
        SNMP agent starts running or stops running. This is usually enabled
        by default on a BIG-IP.
    choices:
      - enabled
      - disabled
  agent_authentication_traps:
    description:
      - When C(enabled), ensures that the system sends authentication warning
        traps to the trap destinations. This is usually disabled by default on
        a BIG-IP.
    choices:
      - enabled
      - disabled
  device_warning_traps:
    description:
      - When C(enabled), ensures that the system sends device warning traps
        to the trap destinations. This is usually enabled by default on a
        BIG-IP.
    choices:
      - enabled
      - disabled
  location:
    description:
      - Specifies the description of this system's physical location.
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set snmp contact
  bigip_snmp:
    contact: Joe User
    password: secret
    server: lb.mydomain.com
    user: admin
    validate_certs: false
  delegate_to: localhost

- name: Set snmp location
  bigip_snmp:
    location: US West 1
    password: secret
    server: lb.mydomain.com
    user: admin
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
agent_status_traps:
  description: Value that the agent status traps was set to.
  returned: changed
  type: string
  sample: enabled
agent_authentication_traps:
  description: Value that the authentication status traps was set to.
  returned: changed
  type: string
  sample: enabled
device_warning_traps:
  description: Value that the warning status traps was set to.
  returned: changed
  type: string
  sample: enabled
contact:
  description: The new value for the person who administers SNMP on the device.
  returned: changed
  type: string
  sample: Joe User
location:
  description: The new value for the system's physical location.
  returned: changed
  type: string
  sample: US West 1a
'''

from ansible.module_utils.basic import AnsibleModule

HAS_DEVEL_IMPORTS = False

try:
    # Sideband repository used for dev
    from library.module_utils.network.f5.bigip import HAS_F5SDK
    from library.module_utils.network.f5.bigip import F5Client
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import cleanup_tokens
    from library.module_utils.network.f5.common import fqdn_name
    from library.module_utils.network.f5.common import f5_argument_spec
    try:
        from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False
    HAS_DEVEL_IMPORTS = True
except ImportError:
    # Upstream Ansible
    from ansible.module_utils.network.f5.bigip import HAS_F5SDK
    from ansible.module_utils.network.f5.bigip import F5Client
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import cleanup_tokens
    from ansible.module_utils.network.f5.common import fqdn_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    try:
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
    except ImportError:
        HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'agentTrap': 'agent_status_traps',
        'authTrap': 'agent_authentication_traps',
        'bigipTraps': 'device_warning_traps',
        'sysLocation': 'location',
        'sysContact': 'contact'
    }

    updatables = [
        'agent_status_traps', 'agent_authentication_traps',
        'device_warning_traps', 'location', 'contact'
    ]

    returnables = [
        'agent_status_traps', 'agent_authentication_traps',
        'device_warning_traps', 'location', 'contact'
    ]

    api_attributes = [
        'agentTrap', 'authTrap', 'bigipTraps', 'sysLocation', 'sysContact'
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result


class Changes(Parameters):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = Parameters(params=self.module.params)
        self.changes = Changes()

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

    def exec_module(self):
        result = dict()

        try:
            changed = self.update()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        changes = self.changes.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        return result

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

    def update_on_device(self):
        params = self.want.api_params()
        result = self.client.api.tm.sys.snmp.load()
        result.modify(**params)

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.snmp.load()
        result = resource.attrs
        return Parameters(params=result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.choices = ['enabled', 'disabled']
        argument_spec = dict(
            contact=dict(),
            agent_status_traps=dict(
                choices=self.choices
            ),
            agent_authentication_traps=dict(
                choices=self.choices
            ),
            device_warning_traps=dict(
                choices=self.choices
            ),
            location=dict()
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
