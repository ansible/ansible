#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2016, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = r'''
---
module: bigip_sys_global
short_description: Manage BIG-IP global settings
description:
  - Manage BIG-IP global settings.
version_added: 2.3
options:
  banner_text:
    description:
      - Specifies the text to present in the advisory banner.
    type: str
  console_timeout:
    description:
      - Specifies the number of seconds of inactivity before the system logs
        off a user that is logged on.
    type: int
  gui_setup:
    description:
      - C(yes) or C(no) the Setup utility in the browser-based
        Configuration utility.
    type: bool
  lcd_display:
    description:
      - Specifies, when C(yes), that the system menu displays on the
        LCD screen on the front of the unit. This setting has no effect
        when used on the VE platform.
    type: bool
  mgmt_dhcp:
    description:
      - Specifies whether or not to enable DHCP client on the management
        interface
    type: bool
  net_reboot:
    description:
      - Specifies, when C(yes), that the next time you reboot the system,
        the system boots to an ISO image on the network, rather than an
        internal media drive.
    type: bool
  quiet_boot:
    description:
      - Specifies, when C(yes), that the system suppresses informational
        text on the console during the boot cycle. When C(no), the
        system presents messages and informational text on the console during
        the boot cycle.
    type: bool
  security_banner:
    description:
      - Specifies whether the system displays an advisory message on the
        login screen.
    type: bool
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value).
    type: str
    choices:
      - present
    default: present
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
  - Wojciech Wypior (@wojtek0806)
'''

EXAMPLES = r'''
- name: Disable the setup utility
  bigip_sys_global:
    gui_setup: no
    provider:
      password: secret
      server: lb.mydomain.com
      user: admin
  delegate_to: localhost
'''

RETURN = r'''
banner_text:
  description: The new text to present in the advisory banner.
  returned: changed
  type: str
  sample: This is a corporate device. Do not touch.
console_timeout:
  description:
    - The new number of seconds of inactivity before the system
      logs off a user that is logged on.
  returned: changed
  type: int
  sample: 600
gui_setup:
  description: The new setting for the Setup utility.
  returned: changed
  type: bool
  sample: yes
lcd_display:
  description: The new setting for displaying the system menu on the LCD.
  returned: changed
  type: bool
  sample: yes
mgmt_dhcp:
  description: The new setting for whether the mgmt interface should DHCP or not.
  returned: changed
  type: bool
  sample: yes
net_reboot:
  description: The new setting for whether the system should boot to an ISO on the network or not.
  returned: changed
  type: bool
  sample: yes
quiet_boot:
  description:
    - The new setting for whether the system should suppress information to
      the console during boot or not.
  returned: changed
  type: bool
  sample: yes
security_banner:
  description:
    - The new setting for whether the system should display an advisory message
      on the login screen or not.
  returned: changed
  type: bool
  sample: yes
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from library.module_utils.network.f5.bigip import F5RestClient
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import AnsibleF5Parameters
    from library.module_utils.network.f5.common import f5_argument_spec
    from library.module_utils.network.f5.common import flatten_boolean
except ImportError:
    from ansible.module_utils.network.f5.bigip import F5RestClient
    from ansible.module_utils.network.f5.common import F5ModuleError
    from ansible.module_utils.network.f5.common import AnsibleF5Parameters
    from ansible.module_utils.network.f5.common import f5_argument_spec
    from ansible.module_utils.network.f5.common import flatten_boolean


class Parameters(AnsibleF5Parameters):
    api_map = {
        'guiSecurityBanner': 'security_banner',
        'guiSecurityBannerText': 'banner_text',
        'guiSetup': 'gui_setup',
        'lcdDisplay': 'lcd_display',
        'mgmtDhcp': 'mgmt_dhcp',
        'netReboot': 'net_reboot',
        'quietBoot': 'quiet_boot',
        'consoleInactivityTimeout': 'console_timeout',
    }

    api_attributes = [
        'guiSecurityBanner',
        'guiSecurityBannerText',
        'guiSetup',
        'lcdDisplay',
        'mgmtDhcp',
        'netReboot',
        'quietBoot',
        'consoleInactivityTimeout',
    ]

    returnables = [
        'security_banner',
        'banner_text',
        'gui_setup',
        'lcd_display',
        'mgmt_dhcp',
        'net_reboot',
        'quiet_boot',
        'console_timeout',
    ]

    updatables = [
        'security_banner',
        'banner_text',
        'gui_setup',
        'lcd_display',
        'mgmt_dhcp',
        'net_reboot',
        'quiet_boot',
        'console_timeout',
    ]

    @property
    def security_banner(self):
        return flatten_boolean(self._values['security_banner'])

    @property
    def gui_setup(self):
        return flatten_boolean(self._values['gui_setup'])

    @property
    def lcd_display(self):
        return flatten_boolean(self._values['lcd_display'])

    @property
    def mgmt_dhcp(self):
        return flatten_boolean(self._values['mgmt_dhcp'])

    @property
    def net_reboot(self):
        return flatten_boolean(self._values['net_reboot'])

    @property
    def quiet_boot(self):
        return flatten_boolean(self._values['quiet_boot'])


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
    @property
    def security_banner(self):
        if self._values['security_banner'] is None:
            return None
        if self._values['security_banner'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def gui_setup(self):
        if self._values['gui_setup'] is None:
            return None
        if self._values['gui_setup'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def lcd_display(self):
        if self._values['lcd_display'] is None:
            return None
        if self._values['lcd_display'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def mgmt_dhcp(self):
        if self._values['mgmt_dhcp'] is None:
            return None
        if self._values['mgmt_dhcp'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def net_reboot(self):
        if self._values['net_reboot'] is None:
            return None
        if self._values['net_reboot'] == 'yes':
            return 'enabled'
        return 'disabled'

    @property
    def quiet_boot(self):
        if self._values['quiet_boot'] is None:
            return None
        if self._values['quiet_boot'] == 'yes':
            return 'enabled'
        return 'disabled'


class ReportableChanges(Changes):
    @property
    def security_banner(self):
        return flatten_boolean(self._values['security_banner'])

    @property
    def gui_setup(self):
        return flatten_boolean(self._values['gui_setup'])

    @property
    def lcd_display(self):
        return flatten_boolean(self._values['lcd_display'])

    @property
    def mgmt_dhcp(self):
        return flatten_boolean(self._values['mgmt_dhcp'])

    @property
    def net_reboot(self):
        return flatten_boolean(self._values['net_reboot'])

    @property
    def quiet_boot(self):
        return flatten_boolean(self._values['quiet_boot'])


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
        want = getattr(self.want, param)
        try:
            have = getattr(self.have, param)
            if want != have:
                return want
        except AttributeError:
            return want


class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.get('module', None)
        self.client = F5RestClient(**self.module.params)
        self.want = ModuleParameters(params=self.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(params=changed)

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

    def should_update(self):
        result = self._update_changed_options()
        if result:
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
            self.module.deprecate(
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

    def read_current_from_device(self):
        uri = "https://{0}:{1}/mgmt/tm/sys/global-settings/".format(
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

    def update_on_device(self):
        params = self.changes.api_params()
        uri = "https://{0}:{1}/mgmt/tm/sys/global-settings/".format(
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


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.states = ['present']
        argument_spec = dict(
            security_banner=dict(
                type='bool'
            ),
            banner_text=dict(),
            gui_setup=dict(
                type='bool'
            ),
            lcd_display=dict(
                type='bool'
            ),
            mgmt_dhcp=dict(
                type='bool'
            ),
            net_reboot=dict(
                type='bool'
            ),
            quiet_boot=dict(
                type='bool'
            ),
            console_timeout=dict(
                type='int'
            ),
            state=dict(
                default='present', choices=['present']
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
