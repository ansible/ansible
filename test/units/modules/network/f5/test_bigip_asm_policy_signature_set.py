# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, F5 Networks Inc.
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
    from library.modules.bigip_asm_policy_signature_set import ApiParameters
    from library.modules.bigip_asm_policy_signature_set import ModuleParameters
    from library.modules.bigip_asm_policy_signature_set import ModuleManager
    from library.modules.bigip_asm_policy_signature_set import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_asm_policy_signature_set import ApiParameters
    from ansible.modules.network.f5.bigip_asm_policy_signature_set import ModuleParameters
    from ansible.modules.network.f5.bigip_asm_policy_signature_set import ModuleManager
    from ansible.modules.network.f5.bigip_asm_policy_signature_set import ArgumentSpec

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
            name='IIS and Windows Signatures',
            state='present',
            policy_name='fake_policy',
            alarm='yes',
            block='no',
            learn='yes'
        )
        try:
            self.p1 = patch('library.modules.bigip_asm_policy_signature_set.tmos_version')
            self.m1 = self.p1.start()
            self.m1.return_value = '13.1.0'
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_asm_policy_signature_set.tmos_version')
            self.m1 = self.p1.start()
            self.m1.return_value = '13.1.0'

        p = ModuleParameters(params=args)

        assert p.name == 'IIS and Windows Signatures'
        assert p.state == 'present'
        assert p.policy_name == 'fake_policy'
        assert p.alarm is True
        assert p.block is False
        assert p.learn is True

        self.p1.stop()


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_asm_policy_signature_set.module_provisioned')
            self.p2 = patch('library.modules.bigip_asm_policy_signature_set.tmos_version')
            self.m1 = self.p1.start()
            self.m2 = self.p2.start()
            self.m2.return_value = '13.1.0'
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_asm_policy_signature_set.module_provisioned')
            self.p2 = patch('ansible.modules.network.f5.bigip_asm_policy_signature_set.tmos_version')
            self.m1 = self.p1.start()
            self.m2 = self.p2.start()
            self.m2.return_value = '13.1.0'
            self.m1.return_value = True

    def tearDown(self):
        self.p1.stop()
        self.p2.stop()

    def test_add_server_technology(self, *args):
        set_module_args(dict(
            policy_name='fake_policy',
            state='present',
            name='IIS and Windows Signatures',
            alarm='yes',
            block='no',
            learn='yes',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'IIS and Windows Signatures'
        assert results['policy_name'] == 'fake_policy'
        assert results['alarm'] == 'yes'
        assert results['block'] == 'no'
        assert results['learn'] == 'yes'
