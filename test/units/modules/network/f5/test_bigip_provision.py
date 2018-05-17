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
    from library.modules.bigip_provision import Parameters
    from library.modules.bigip_provision import ModuleManager
    from library.modules.bigip_provision import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_provision import Parameters
        from ansible.modules.network.f5.bigip_provision import ModuleManager
        from ansible.modules.network.f5.bigip_provision import ArgumentSpec
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
            module='gtm',
            password='password',
            server='localhost',
            user='admin'
        )
        p = Parameters(params=args)
        assert p.module == 'gtm'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_provision_one_module_default_level(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            module='gtm',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = Parameters(
            dict(
                module='gtm',
                level='none'
            )
        )
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.reboot_device = Mock(return_value=True)
        mm.save_on_device = Mock(return_value=True)

        # this forced sleeping can cause these tests to take 15
        # or more seconds to run. This is deliberate.
        mm._is_mprov_running_on_device = Mock(side_effect=[True, False, False, False, False])

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['level'] == 'nominal'

    def test_provision_all_modules(self, *args):
        modules = [
            'afm', 'am', 'sam', 'asm', 'avr', 'fps',
            'gtm', 'lc', 'ltm', 'pem', 'swg', 'ilx',
            'apm',
        ]

        for module in modules:
            # Configure the arguments that would be sent to the Ansible module
            set_module_args(dict(
                module=module,
                password='passsword',
                server='localhost',
                user='admin'
            ))

            with patch('ansible.module_utils.basic.AnsibleModule.fail_json') as mo:
                AnsibleModule(
                    argument_spec=self.spec.argument_spec,
                    supports_check_mode=self.spec.supports_check_mode,
                )
                mo.assert_not_called()
