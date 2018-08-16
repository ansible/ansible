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
module: bigip_device_sshd
short_description: Manage the SSHD settings of a BIG-IP
description:
  - Manage the SSHD settings of a BIG-IP.
version_added: 2.2
options:
  allow:
    description:
      - Specifies, if you have enabled SSH access, the IP address or address
        range for other systems that can use SSH to communicate with this
        system.
      - To specify all addresses, use the value C(all).
      - IP address can be specified, such as 172.27.1.10.
      - IP rangees can be specified, such as 172.27.*.* or 172.27.0.0/255.255.0.0.
  banner:
    description:
      - Whether to enable the banner or not.
    choices:
      - enabled
      - disabled
  banner_text:
    description:
      - Specifies the text to include on the pre-login banner that displays
        when a user attempts to login to the system using SSH.
  inactivity_timeout:
    description:
      - Specifies the number of seconds before inactivity causes an SSH
        session to log out.
  log_level:
    description:
      - Specifies the minimum SSHD message level to include in the system log.
    choices:
      - debug
      - debug1
      - debug2
      - debug3
      - error
      - fatal
      - info
      - quiet
      - verbose
  login:
    description:
      - Specifies, when checked C(enabled), that the system accepts SSH
        communications.
    choices:
      - enabled
      - disabled
  port:
    description:
      - Port that you want the SSH daemon to run on.
notes:
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Set the banner for the SSHD service from a string
  bigip_device_sshd:
    banner: enabled
    banner_text: banner text goes here
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Set the banner for the SSHD service from a file
  bigip_device_sshd:
    banner: enabled
    banner_text: "{{ lookup('file', '/path/to/file') }}"
    password: secret
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost

- name: Set the SSHD service to run on port 2222
  bigip_device_sshd:
    password: secret
    port: 2222
    server: lb.mydomain.com
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
allow:
  description: >
    Specifies, if you have enabled SSH access, the IP address or address
    range for other systems that can use SSH to communicate with this
    system.
  returned: changed
  type: string
  sample: 192.0.2.*
banner:
  description: Whether the banner is enabled or not.
  returned: changed
  type: string
  sample: true
banner_text:
  description: >
    Specifies the text included on the pre-login banner that
    displays when a user attempts to login to the system using SSH.
  returned: changed and success
  type: string
  sample: This is a corporate device. Connecting to it without...
inactivity_timeout:
  description: >
    The number of seconds before inactivity causes an SSH
    session to log out.
  returned: changed
  type: int
  sample: 10
log_level:
  description: The minimum SSHD message level to include in the system log.
  returned: changed
  type: string
  sample: debug
login:
  description: Specifies that the system accepts SSH communications or not.
  returned: changed
  type: bool
  sample: true
port:
  description: Port that you want the SSH daemon to run on.
  returned: changed
  type: int
  sample: 22
'''

from ansible.module_utils.basic import AnsibleModule

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
        'bannerText': 'banner_text',
        'inactivityTimeout': 'inactivity_timeout',
        'logLevel': 'log_level'
    }

    api_attributes = [
        'allow', 'banner', 'bannerText', 'inactivityTimeout', 'logLevel',
        'login', 'port'
    ]

    updatables = [
        'allow', 'banner', 'banner_text', 'inactivity_timeout', 'log_level',
        'login', 'port'
    ]

    returnables = [
        'allow', 'banner', 'banner_text', 'inactivity_timeout', 'log_level',
        'login', 'port'
    ]

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    @property
    def inactivity_timeout(self):
        if self._values['inactivity_timeout'] is None:
            return None
        return int(self._values['inactivity_timeout'])

    @property
    def port(self):
        if self._values['port'] is None:
            return None
        return int(self._values['port'])

    @property
    def allow(self):
        if self._values['allow'] is None:
            return None
        allow = self._values['allow']
        result = list(set([str(x) for x in allow]))
        result = sorted(result)
        return result


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    pass


class Changes(Parameters):
    pass


class UsableChanges(Changes):
    pass


class ReportableChanges(Changes):
    pass


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = kwargs.get('client', None)
        self.have = None
        self.want = ModuleParameters(params=self.module.params)
        self.changes = UsableChanges()

    def _update_changed_options(self):
        changed = {}
        for key in Parameters.updatables:
            if getattr(self.want, key) is not None:
                attr1 = getattr(self.want, key)
                attr2 = getattr(self.have, key)
                if attr1 != attr2:
                    changed[key] = attr1
        if changed:
            self.changes = UsableChanges(params=changed)
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

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.sshd.load()
        result = resource.attrs
        return ApiParameters(params=result)

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
        resource = self.client.api.tm.sys.sshd.load()
        resource.update(**params)


class ArgumentSpec(object):
    def __init__(self):
        self.choices = ['enabled', 'disabled']
        self.levels = [
            'debug', 'debug1', 'debug2', 'debug3', 'error', 'fatal', 'info',
            'quiet', 'verbose'
        ]
        self.supports_check_mode = True
        argument_spec = dict(
            allow=dict(
                type='list'
            ),
            banner=dict(
                choices=self.choices
            ),
            banner_text=dict(),
            inactivity_timeout=dict(
                type='int'
            ),
            log_level=dict(
                choices=self.levels
            ),
            login=dict(
                choices=self.choices
            ),
            port=dict(
                type='int'
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
