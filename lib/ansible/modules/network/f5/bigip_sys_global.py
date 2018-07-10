#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

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
  console_timeout:
    description:
      - Specifies the number of seconds of inactivity before the system logs
        off a user that is logged on.
  gui_setup:
    description:
      - C(enable) or C(disabled) the Setup utility in the browser-based
        Configuration utility.
    type: bool
  lcd_display:
    description:
      - Specifies, when C(enabled), that the system menu displays on the
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
      - Specifies, when C(enabled), that the next time you reboot the system,
        the system boots to an ISO image on the network, rather than an
        internal media drive.
    type: bool
  quiet_boot:
    description:
      - Specifies, when C(enabled), that the system suppresses informational
        text on the console during the boot cycle. When C(disabled), the
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
    default: present
    choices:
      - present
extends_documentation_fragment: f5
requirements:
  - f5-sdk
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Disable the setup utility
  bigip_sys_global:
    gui_setup: disabled
    password: secret
    server: lb.mydomain.com
    user: admin
    state: present
  delegate_to: localhost
'''

RETURN = r'''
banner_text:
  description: The new text to present in the advisory banner.
  returned: changed
  type: string
  sample: This is a corporate device. Do not touch.
console_timeout:
  description: >
    The new number of seconds of inactivity before the system
    logs off a user that is logged on.
  returned: changed
  type: int
  sample: 600
gui_setup:
  description: The new setting for the Setup utility.
  returned: changed
  type: string
  sample: enabled
lcd_display:
  description: The new setting for displaying the system menu on the LCD.
  returned: changed
  type: string
  sample: enabled
mgmt_dhcp:
  description: The new setting for whether the mgmt interface should DHCP or not.
  returned: changed
  type: string
  sample: enabled
net_reboot:
  description: The new setting for whether the system should boot to an ISO on the network or not.
  returned: changed
  type: string
  sample: enabled
quiet_boot:
  description: >
    The new setting for whether the system should suppress information to
    the console during boot or not.
  returned: changed
  type: string
  sample: enabled
security_banner:
  description: >
    The new setting for whether the system should display an advisory message
    on the login screen or not.
  returned: changed
  type: string
  sample: enabled
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.parsing.convert_bool import BOOLEANS
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE

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
        'guiSecurityBanner': 'security_banner',
        'guiSecurityBannerText': 'banner_text',
        'guiSetup': 'gui_setup',
        'lcdDisplay': 'lcd_display',
        'mgmtDhcp': 'mgmt_dhcp',
        'netReboot': 'net_reboot',
        'quietBoot': 'quiet_boot',
        'consoleInactivityTimeout': 'console_timeout'
    }

    api_attributes = [
        'guiSecurityBanner', 'guiSecurityBannerText', 'guiSetup', 'lcdDisplay',
        'mgmtDhcp', 'netReboot', 'quietBoot', 'consoleInactivityTimeout'
    ]

    returnables = [
        'security_banner', 'banner_text', 'gui_setup', 'lcd_display',
        'mgmt_dhcp', 'net_reboot', 'quiet_boot', 'console_timeout'
    ]

    updatables = [
        'security_banner', 'banner_text', 'gui_setup', 'lcd_display',
        'mgmt_dhcp', 'net_reboot', 'quiet_boot', 'console_timeout'
    ]


class ApiParameters(Parameters):
    pass


class ModuleParameters(Parameters):
    def _get_boolean_like_return_value(self, parameter):
        if self._values[parameter] is None:
            return None
        elif self._values[parameter] in ['enabled', 'disabled']:
            self._values['__warnings'].append(
                dict(version='2.5', msg='enabled/disabled are deprecated. Use boolean values (true, yes, no, 1, 0) instead.')
            )
        true = list(BOOLEANS_TRUE) + ['True']
        false = list(BOOLEANS_FALSE) + ['False']
        if self._values[parameter] in true:
            return 'enabled'
        if self._values[parameter] in false:
            return 'disabled'
        else:
            return str(self._values[parameter])

    @property
    def security_banner(self):
        result = self._get_boolean_like_return_value('security_banner')
        return result

    @property
    def gui_setup(self):
        result = self._get_boolean_like_return_value('gui_setup')
        return result

    @property
    def banner_text(self):
        result = self._get_boolean_like_return_value('banner_text')
        return result

    @property
    def lcd_display(self):
        result = self._get_boolean_like_return_value('lcd_display')
        return result

    @property
    def mgmt_dhcp(self):
        result = self._get_boolean_like_return_value('mgmt_dhcp')
        return result

    @property
    def net_reboot(self):
        result = self._get_boolean_like_return_value('net_reboot')
        return result

    @property
    def quiet_boot(self):
        result = self._get_boolean_like_return_value('quiet_boot')
        return result


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
        self.client = kwargs.get('client', None)
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

        try:
            changed = self.present()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

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

    def read_current_from_device(self):
        resource = self.client.api.tm.sys.global_settings.load()
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

    def update_on_device(self):
        params = self.want.api_params()
        resource = self.client.api.tm.sys.global_settings.load()
        resource.modify(**params)


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
            console_timeout=dict(required=False, type='int', default=None),
            state=dict(default='present', choices=['present'])
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
