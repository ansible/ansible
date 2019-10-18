# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json
import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("F5 Ansible modules require Python >= 2.7")

from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_provision import ModuleParameters
    from library.modules.bigip_provision import ModuleManager
    from library.modules.bigip_provision import ArgumentSpec
    from library.modules.bigip_provision import ApiParameters

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_provision import ModuleParameters
    from ansible.modules.network.f5.bigip_provision import ModuleManager
    from ansible.modules.network.f5.bigip_provision import ArgumentSpec
    from ansible.modules.network.f5.bigip_provision import ApiParameters

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch

    from units.modules.utils import set_module_args


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
            level='nominal',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'gtm'
        assert p.level == 'nominal'

    def test_api_parameters(self):
        args = load_fixture('load_sys_provision_default.json')
        p = ApiParameters(params=args)
        assert p.level == 'dedicated'
        assert p.memory == 'medium'
        assert p.module == 'urldb'

    def test_module_parameters_level_minimum(self):
        args = dict(
            level='minimum',
        )
        p = ModuleParameters(params=args)
        assert p.level == 'minimum'

    def test_module_parameters_level_nominal(self):
        args = dict(
            level='nominal',
        )
        p = ModuleParameters(params=args)
        assert p.level == 'nominal'

    def test_module_parameters_level_dedicated(self):
        args = dict(
            level='dedicated',
        )
        p = ModuleParameters(params=args)
        assert p.level == 'dedicated'

    def test_module_parameters_memory_small(self):
        args = dict(
            module='mgmt',
            memory='small',
        )
        p = ModuleParameters(params=args)
        assert p.memory == 0

    def test_module_parameters_memory_medium(self):
        args = dict(
            module='mgmt',
            memory='medium',
        )
        p = ModuleParameters(params=args)
        assert p.memory == 200

    def test_module_parameters_memory_large(self):
        args = dict(
            module='mgmt',
            memory='large',
        )
        p = ModuleParameters(params=args)
        assert p.memory == 500

    def test_module_parameters_memory_700(self):
        args = dict(
            module='mgmt',
            memory=700,
        )
        p = ModuleParameters(params=args)
        assert p.memory == 700

    def test_module_parameters_mod_afm(self):
        args = dict(
            module='afm',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'afm'

    def test_module_parameters_mod_am(self):
        args = dict(
            module='am',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'am'

    def test_module_parameters_mod_sam(self):
        args = dict(
            module='sam',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'sam'

    def test_module_parameters_mod_asm(self):
        args = dict(
            module='asm',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'asm'

    def test_module_parameters_mod_avr(self):
        args = dict(
            module='avr',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'avr'

    def test_module_parameters_mod_fps(self):
        args = dict(
            module='fps',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'fps'

    def test_module_parameters_mod_gtm(self):
        args = dict(
            module='gtm',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'gtm'

    def test_module_parameters_mod_lc(self):
        args = dict(
            module='lc',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'lc'

    def test_module_parameters_mod_pem(self):
        args = dict(
            module='pem',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'pem'

    def test_module_parameters_mod_swg(self):
        args = dict(
            module='swg',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'swg'

    def test_module_parameters_mod_ilx(self):
        args = dict(
            module='ilx',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'ilx'

    def test_module_parameters_mod_apm(self):
        args = dict(
            module='apm',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'apm'

    def test_module_parameters_mod_mgmt(self):
        args = dict(
            module='mgmt',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'mgmt'

    def test_module_parameters_mod_sslo(self):
        args = dict(
            module='sslo',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'sslo'

    def test_module_parameters_mod_urldb(self):
        args = dict(
            module='urldb',
        )
        p = ModuleParameters(params=args)
        assert p.module == 'urldb'


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
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        # Configure the parameters that would be returned by querying the
        # remote device
        current = ModuleParameters(
            dict(
                module='gtm',
                level='none'
            )
        )
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive
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
            'apm', 'mgmt', 'sslo', 'urldb',
        ]

        for module in modules:
            # Configure the arguments that would be sent to the Ansible module
            set_module_args(dict(
                module=module,
                provider=dict(
                    server='localhost',
                    password='password',
                    user='admin'
                )
            ))

            with patch('ansible.module_utils.basic.AnsibleModule.fail_json') as mo:
                AnsibleModule(
                    argument_spec=self.spec.argument_spec,
                    supports_check_mode=self.spec.supports_check_mode,
                    mutually_exclusive=self.spec.mutually_exclusive
                )
                mo.assert_not_called()
