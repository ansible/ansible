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
module: bigip_sys_global
short_description: Manage BIG-IP global settings.
description:
  - Manage BIG-IP global settings.
version_added: "2.3"
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
        Configuration utility
    choices:
      - enabled
      - disabled
  lcd_display:
    description:
      - Specifies, when C(enabled), that the system menu displays on the
        LCD screen on the front of the unit. This setting has no effect
        when used on the VE platform.
    choices:
      - enabled
      - disabled
  mgmt_dhcp:
    description:
      - Specifies whether or not to enable DHCP client on the management
        interface
    choices:
      - enabled
      - disabled
  net_reboot:
    description:
      - Specifies, when C(enabled), that the next time you reboot the system,
        the system boots to an ISO image on the network, rather than an
        internal media drive.
    choices:
      - enabled
      - disabled
  quiet_boot:
    description:
      - Specifies, when C(enabled), that the system suppresses informational
        text on the console during the boot cycle. When C(disabled), the
        system presents messages and informational text on the console during
        the boot cycle.
  security_banner:
    description:
      - Specifies whether the system displays an advisory message on the
        login screen.
    choices:
      - enabled
      - disabled
  state:
    description:
      - The state of the variable on the system. When C(present), guarantees
        that an existing variable is set to C(value).
    required: false
    default: present
    choices:
      - present
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
- name: Disable the setup utility
  bigip_sys_global:
      gui_setup: "disabled"
      password: "secret"
      server: "lb.mydomain.com"
      user: "admin"
      state: "present"
  delegate_to: localhost
'''

RETURN = '''
banner_text:
    description: The new text to present in the advisory banner.
    returned: changed
    type: string
    sample: "This is a corporate device. Do not touch."
console_timeout:
    description: >
      The new number of seconds of inactivity before the system
      logs off a user that is logged on.
    returned: changed
    type: integer
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
    description: >
      The new setting for whether the mgmt interface should DHCP
      or not
    returned: changed
    type: string
    sample: enabled
net_reboot:
    description: >
      The new setting for whether the system should boot to an ISO on the
      network or not
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
      on the login screen or not
    returned: changed
    type: string
    sample: enabled
'''

try:
    from f5.bigip.contexts import TransactionContextManager
    from f5.bigip import ManagementRoot
    from icontrol.session import iControlUnexpectedHTTPError
    HAS_F5SDK = True
except ImportError:
    HAS_F5SDK = False


class BigIpSysGlobalManager(object):
    def __init__(self, *args, **kwargs):
        self.changed_params = dict()
        self.params = kwargs
        self.api = None

    def apply_changes(self):
        result = dict()

        changed = self.apply_to_running_config()

        result.update(**self.changed_params)
        result.update(dict(changed=changed))
        return result

    def apply_to_running_config(self):
        try:
            self.api = self.connect_to_bigip(**self.params)
            return self.update_sys_global_settings()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

    def connect_to_bigip(self, **kwargs):
        return ManagementRoot(kwargs['server'],
                              kwargs['user'],
                              kwargs['password'],
                              port=kwargs['server_port'])

    def read_sys_global_information(self):
        settings = self.load_sys_global()
        return self.format_sys_global_information(settings)

    def load_sys_global(self):
        return self.api.tm.sys.global_settings.load()

    def get_changed_parameters(self):
        result = dict()
        current = self.read_sys_global_information()
        if self.security_banner_is_changed(current):
            result['guiSecurityBanner'] = self.params['security_banner']
        if self.banner_text_is_changed(current):
            result['guiSecurityBannerText'] = self.params['banner_text']
        if self.gui_setup_is_changed(current):
            result['guiSetup'] = self.params['gui_setup']
        if self.lcd_display_is_changed(current):
            result['lcdDisplay'] = self.params['lcd_display']
        if self.mgmt_dhcp_is_changed(current):
            result['mgmtDhcp'] = self.params['mgmt_dhcp']
        if self.net_reboot_is_changed(current):
            result['netReboot'] = self.params['net_reboot']
        if self.quiet_boot_is_changed(current):
            result['quietBoot'] = self.params['quiet_boot']
        if self.console_timeout_is_changed(current):
            result['consoleInactivityTimeout'] = self.params['console_timeout']
        return result

    def security_banner_is_changed(self, current):
        if self.params['security_banner'] is None:
            return False
        if 'security_banner' not in current:
            return True
        if self.params['security_banner'] == current['security_banner']:
            return False
        else:
            return True

    def banner_text_is_changed(self, current):
        if self.params['banner_text'] is None:
            return False
        if 'banner_text' not in current:
            return True
        if self.params['banner_text'] == current['banner_text']:
            return False
        else:
            return True

    def gui_setup_is_changed(self, current):
        if self.params['gui_setup'] is None:
            return False
        if 'gui_setup' not in current:
            return True
        if self.params['gui_setup'] == current['gui_setup']:
            return False
        else:
            return True

    def lcd_display_is_changed(self, current):
        if self.params['lcd_display'] is None:
            return False
        if 'lcd_display' not in current:
            return True
        if self.params['lcd_display'] == current['lcd_display']:
            return False
        else:
            return True

    def mgmt_dhcp_is_changed(self, current):
        if self.params['mgmt_dhcp'] is None:
            return False
        if 'mgmt_dhcp' not in current:
            return True
        if self.params['mgmt_dhcp'] == current['mgmt_dhcp']:
            return False
        else:
            return True

    def net_reboot_is_changed(self, current):
        if self.params['net_reboot'] is None:
            return False
        if 'net_reboot' not in current:
            return True
        if self.params['net_reboot'] == current['net_reboot']:
            return False
        else:
            return True

    def quiet_boot_is_changed(self, current):
        if self.params['quiet_boot'] is None:
            return False
        if 'quiet_boot' not in current:
            return True
        if self.params['quiet_boot'] == current['quiet_boot']:
            return False
        else:
            return True

    def console_timeout_is_changed(self, current):
        if self.params['console_timeout'] is None:
            return False
        if 'console_timeout' not in current:
            return True
        if self.params['console_timeout'] == current['console_timeout']:
            return False
        else:
            return True

    def format_sys_global_information(self, settings):
        result = dict()
        if hasattr(settings, 'guiSecurityBanner'):
            result['security_banner'] = str(settings.guiSecurityBanner)
        if hasattr(settings, 'guiSecurityBannerText'):
            result['banner_text'] = str(settings.guiSecurityBannerText)
        if hasattr(settings, 'guiSetup'):
            result['gui_setup'] = str(settings.guiSetup)
        if hasattr(settings, 'lcdDisplay'):
            result['lcd_display'] = str(settings.lcdDisplay)
        if hasattr(settings, 'mgmtDhcp'):
            result['mgmt_dhcp'] = str(settings.mgmtDhcp)
        if hasattr(settings, 'netReboot'):
            result['net_reboot'] = str(settings.netReboot)
        if hasattr(settings, 'quietBoot'):
            result['quiet_boot'] = str(settings.quietBoot)
        if hasattr(settings, 'consoleInactivityTimeout'):
            result['console_timeout'] = int(settings.consoleInactivityTimeout)
        return result

    def update_sys_global_settings(self):
        params = self.get_changed_parameters()
        if params:
            self.changed_params = camel_dict_to_snake_dict(params)
            if self.params['check_mode']:
                return True
        else:
            return False
        self.update_sys_global_settings_on_device(params)
        return True

    def update_sys_global_settings_on_device(self, params):
        tx = self.api.tm.transactions.transaction
        with TransactionContextManager(tx) as api:
            r = api.tm.sys.global_settings.load()
            r.update(**params)


class BigIpSysGlobalModuleConfig(object):
    def __init__(self):
        self.argument_spec = dict()
        self.meta_args = dict()
        self.supports_check_mode = True
        self.states = ['present']
        self.on_off_choices = ['enabled', 'disabled']

        self.initialize_meta_args()
        self.initialize_argument_spec()

    def initialize_meta_args(self):
        args = dict(
            security_banner=dict(
                required=False,
                choices=self.on_off_choices,
                default=None
            ),
            banner_text=dict(required=False, default=None),
            gui_setup=dict(
                required=False,
                choices=self.on_off_choices,
                default=None
            ),
            lcd_display=dict(
                required=False,
                choices=self.on_off_choices,
                default=None
            ),
            mgmt_dhcp=dict(
                required=False,
                choices=self.on_off_choices,
                default=None
            ),
            net_reboot=dict(
                required=False,
                choices=self.on_off_choices,
                default=None
            ),
            quiet_boot=dict(
                required=False,
                choices=self.on_off_choices,
                default=None
            ),
            console_timeout=dict(required=False, type='int', default=None),
            state=dict(default='present', choices=['present'])
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

    config = BigIpSysGlobalModuleConfig()
    module = config.create()

    try:
        obj = BigIpSysGlobalManager(
            check_mode=module.check_mode, **module.params
        )
        result = obj.apply_changes()

        module.exit_json(**result)
    except F5ModuleError as e:
        module.fail_json(msg=str(e))

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.f5 import *

if __name__ == '__main__':
    main()
