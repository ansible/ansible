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
module: bigip_sys_daemon_log_tmm
short_description: Manage BIG-IP tmm daemon log settings
description:
  - Manage BIG-IP tmm log settings.
version_added: 2.8
options:
  arp_log_level:
    description:
      - Specifies the lowest level of ARP messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - error
      - informational
      - notice
      - warning
  http_compression_log_level:
    description:
      - Specifies the lowest level of HTTP compression messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - error
      - informational
      - notice
      - warning
  http_log_level:
    description:
      - Specifies the lowest level of HTTP messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - error
      - informational
      - notice
      - warning
  ip_log_level:
    description:
      - Specifies the lowest level of IP address messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - informational
      - notice
      - warning
  irule_log_level:
    description:
      - Specifies the lowest level of iRule messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - error
      - informational
      - notice
      - warning
  layer4_log_level:
    description:
      - Specifies the lowest level of Layer 4 messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - informational
      - notice
  net_log_level:
    description:
      - Specifies the lowest level of network messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - critical
      - debug
      - error
      - informational
      - notice
      - warning
  os_log_level:
    description:
      - Specifies the lowest level of operating system messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - alert
      - critical
      - debug
      - emergency
      - error
      - informational
      - notice
      - warning
  pva_log_level:
    description:
      - Specifies the lowest level of PVA messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - debug
      - informational
      - notice
  ssl_log_level:
    description:
      - Specifies the lowest level of SSL messages from the tmm daemon
        to include in the system log.
    type: str
    choices:
      - alert
      - critical
      - debug
      - emergency
      - error
      - informational
      - notice
      - warning
  state:
    description:
      - The state of the log level on the system. When C(present), guarantees
        that an existing log level is set to C(value).
    type: str
    choices:
      - present
    default: present
extends_documentation_fragment: f5
author:
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Set SSL log level to debug
  bigip_sys_daemon_log_tmm:
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
    ssl_log_level: debug
  delegate_to: localhost
'''

RETURN = r'''
arp_log_level:
  description: Lowest level of ARP messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: error
http_compression_log_level:
  description: Lowest level of HTTP compression messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: debug
http_log_level:
  description: Lowest level of HTTP messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: notice
ip_log_level:
  description: Lowest level of IP address messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: warning
irule_log_level:
  description: Lowest level of iRule messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: error
layer4_log_level:
  description: Lowest level of Layer 4 messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: notice
net_log_level:
  description: Lowest level of network messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: critical
os_log_level:
  description: Lowest level of operating system messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: critical
pva_log_level:
  description: Lowest level of PVA messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: debug
ssl_log_level:
  description: Lowest level of SSL messages from the tmm daemon to log.
  returned: changed
  type: str
  sample: critical
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec


class Parameters(AnsibleF5Parameters):
    api_map = {
        'arpLogLevel': 'arp_log_level',
        'httpCompressionLogLevel': 'http_compression_log_level',
        'httpLogLevel': 'http_log_level',
        'ipLogLevel': 'ip_log_level',
        'iruleLogLevel': 'irule_log_level',
        'layer4LogLevel': 'layer4_log_level',
        'netLogLevel': 'net_log_level',
        'osLogLevel': 'os_log_level',
        'pvaLogLevel': 'pva_log_level',
        'sslLogLevel': 'ssl_log_level',
    }

    api_attributes = [
        'arpLogLevel',
        'httpCompressionLogLevel',
        'httpLogLevel',
        'ipLogLevel',
        'iruleLogLevel',
        'layer4LogLevel',
        'netLogLevel',
        'osLogLevel',
        'pvaLogLevel',
        'sslLogLevel',
    ]

    returnables = [
        'arp_log_level',
        'http_compression_log_level',
        'http_log_level',
        'ip_log_level',
        'irule_log_level',
        'layer4_log_level',
        'net_log_level',
        'os_log_level',
        'pva_log_level',
        'ssl_log_level',
    ]

    updatables = [
        'arp_log_level',
        'http_compression_log_level',
        'http_log_level',
        'ip_log_level',
        'irule_log_level',
        'layer4_log_level',
        'net_log_level',
        'os_log_level',
        'pva_log_level',
        'ssl_log_level',
    ]


class ApiParameters(Parameters):
    pass


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

    def exec_module(self):
        result = dict()

        changed = self.present()

        reportable = ReportableChanges(params=self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

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
        uri = "https://{0}:{1}/mgmt/tm/sys/daemon-log-settings/tmm".format(
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
        uri = "https://{0}:{1}/mgmt/tm/sys/daemon-log-settings/tmm".format(
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
        self.choices_min = ['debug', 'informational', 'notice']
        self.choices_common = self.choices_min + ['warning', 'error']
        self.choices_all = self.choices_common + ['alert', 'critical', 'emergency']
        argument_spec = dict(
            arp_log_level=dict(
                choices=self.choices_common
            ),
            http_compression_log_level=dict(
                choices=self.choices_common
            ),
            http_log_level=dict(
                choices=self.choices_common
            ),
            ip_log_level=dict(
                choices=self.choices_min + ['warning']
            ),
            irule_log_level=dict(
                choices=self.choices_common
            ),
            layer4_log_level=dict(
                choices=self.choices_min
            ),
            net_log_level=dict(
                choices=self.choices_common + ['critical']
            ),
            os_log_level=dict(
                choices=self.choices_all
            ),
            pva_log_level=dict(
                choices=self.choices_min
            ),
            ssl_log_level=dict(
                choices=self.choices_all
            ),
            state=dict(default='present', choices=['present'])
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
