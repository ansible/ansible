#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}

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
      - To remove SSH access specify an empty list or an empty string.
    type: list
  banner:
    description:
      - Whether to enable the banner or not.
    type: str
    choices:
      - enabled
      - disabled
  banner_text:
    description:
      - Specifies the text to include on the pre-login banner that displays
        when a user attempts to login to the system using SSH.
    type: str
  inactivity_timeout:
    description:
      - Specifies the number of seconds before inactivity causes an SSH
        session to log out.
    type: int
  log_level:
    description:
      - Specifies the minimum SSHD message level to include in the system log.
    type: str
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
    type: str
    choices:
      - enabled
      - disabled
  port:
    description:
      - Port that you want the SSH daemon to run on.
    type: int
notes:
  - Requires BIG-IP version 12.0.0 or greater
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Set the banner for the SSHD service from a string
  bigip_device_sshd:
    banner: enabled
    banner_text: banner text goes here
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Set the banner for the SSHD service from a file
  bigip_device_sshd:
    banner: enabled
    banner_text: "{{ lookup('file', '/path/to/file') }}"
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost

- name: Set the SSHD service to run on port 2222
  bigip_device_sshd:
    port: 2222
    provider:
      user: admin
      password: secret
      server: lb.mydomain.com
  delegate_to: localhost
'''

RETURN = r'''
allow:
  description:
    - Specifies, if you have enabled SSH access, the IP address or address
      range for other systems that can use SSH to communicate with this
      system.
  returned: changed
  type: list
  sample: 192.0.2.*
banner:
  description: Whether the banner is enabled or not.
  returned: changed
  type: str
  sample: true
banner_text:
  description:
    - Specifies the text included on the pre-login banner that
      displays when a user attempts to login to the system using SSH.
  returned: changed and success
  type: str
  sample: This is a corporate device. Connecting to it without...
inactivity_timeout:
  description:
    - The number of seconds before inactivity causes an SSH
      session to log out.
  returned: changed
  type: int
  sample: 10
log_level:
  description: The minimum SSHD message level to include in the system log.
  returned: changed
  type: str
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
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import fq_name
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import is_empty_list
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import fq_name
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import is_empty_list


class Parameters(AnsibleF5Parameters):
    api_map = {
        'bannerText': 'banner_text',
        'inactivityTimeout': 'inactivity_timeout',
        'logLevel': 'log_level',
    }

    api_attributes = [
        'allow', 'banner', 'bannerText', 'inactivityTimeout',
        'logLevel', 'login', 'port',
    ]

    updatables = [
        'allow', 'banner', 'banner_text', 'inactivity_timeout',
        'log_level', 'login', 'port',
    ]

    returnables = [
        'allow', 'banner', 'banner_text', 'inactivity_timeout',
        'log_level', 'login', 'port',
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
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
        allow = self._values['allow']
        if allow is None:
            return None
        if is_empty_list(allow):
            return []
        return allow


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                change = getattr(self, returnable)
                if isinstance(change, dict):
                    result.update(change)
                else:
                    result[returnable] = change
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class UsableChanges(Changes):
    pass


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
    def allow(self):
        if self.want.allow is None:
            return None
        if not self.want.allow:
            if self.have.allow is None:
                return None
            if self.have.allow is not None:
                return self.want.allow
        if self.have.allow is None:
            return self.want.allow
        if set(self.want.allow) != set(self.have.allow):
            return self.want.allow

    @property
    def banner_text(self):
        if self.want.banner_text is None:
            return None
        if self.want.banner_text == '' and self.have.banner_text is None:
            return None
        if self.want.banner_text != self.have.banner_text:
            return self.want.banner_text


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

    def exec_module(self):
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
        uri = "https://{0}:{1}/mgmt/tm/sys/sshd/".format(
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
        uri = "https://{0}:{1}/mgmt/tm/sys/sshd/".format(
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

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))


if __name__ == '__main__':
    main()
