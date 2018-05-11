# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_sys_global import ApiParameters
    from library.modules.bigip_sys_global import ModuleParameters
    from library.modules.bigip_sys_global import ModuleManager
    from library.modules.bigip_sys_global import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_sys_global import ApiParameters
        from ansible.modules.network.f5.bigip_sys_global import ModuleParameters
        from ansible.modules.network.f5.bigip_sys_global import ModuleManager
        from ansible.modules.network.f5.bigip_sys_global import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            banner_text='this is a banner',
            console_timeout=100,
            gui_setup='yes',
            lcd_display='yes',
            mgmt_dhcp='yes',
            net_reboot='yes',
            quiet_boot='yes',
            security_banner='yes',
        )
        p = ModuleParameters(params=args)
        assert p.banner_text == 'this is a banner'
        assert p.console_timeout == 100
        assert p.gui_setup == 'enabled'
        assert p.lcd_display == 'enabled'
        assert p.mgmt_dhcp == 'enabled'
        assert p.net_reboot == 'enabled'
        assert p.quiet_boot == 'enabled'
        assert p.security_banner == 'enabled'

    def test_api_parameters(self):
        args = load_fixture('load_sys_global_settings.json')
        p = ApiParameters(params=args)
        assert 'Welcome to the BIG-IP Configuration Utility' in p.banner_text
        assert p.console_timeout == 0
        assert p.gui_setup == 'disabled'
        assert p.lcd_display == 'enabled'
        assert p.mgmt_dhcp == 'enabled'
        assert p.net_reboot == 'disabled'
        assert p.quiet_boot == 'enabled'
        assert p.security_banner == 'enabled'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_update(self, *args):
        set_module_args(dict(
            banner_text='this is a banner',
            console_timeout=100,
            password='admin',
            server='localhost',
            user='admin',
            state='present'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ApiParameters(params=load_fixture('load_sys_global_settings.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
