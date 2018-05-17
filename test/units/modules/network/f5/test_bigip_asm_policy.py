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

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import Mock
from ansible.compat.tests.mock import patch
from ansible.module_utils.basic import AnsibleModule

try:
    from library.modules.bigip_asm_policy import V1Parameters
    from library.modules.bigip_asm_policy import V2Parameters
    from library.modules.bigip_asm_policy import ModuleManager
    from library.modules.bigip_asm_policy import V1Manager
    from library.modules.bigip_asm_policy import V2Manager
    from library.modules.bigip_asm_policy import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_asm_policy import V1Parameters
        from ansible.modules.network.f5.bigip_asm_policy import V2Parameters
        from ansible.modules.network.f5.bigip_asm_policy import ModuleManager
        from ansible.modules.network.f5.bigip_asm_policy import V1Manager
        from ansible.modules.network.f5.bigip_asm_policy import V2Manager
        from ansible.modules.network.f5.bigip_asm_policy import ArgumentSpec
        from ansible.module_utils.network.f5.common import F5ModuleError
        from ansible.module_utils.network.f5.common import iControlUnexpectedHTTPError
        from units.modules.utils import set_module_args
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)
    with open(path) as f:
        data = f.read()
    try:
        data = json.loads(data)
    except Exception:
        pass
    return data


class TestParameters(unittest.TestCase):
    def test_module_parameters(self):
        args = dict(
            name='fake_policy',
            state='present',
            file='/var/fake/fake.xml'
        )

        p = V1Parameters(params=args)
        assert p.name == 'fake_policy'
        assert p.state == 'present'
        assert p.file == '/var/fake/fake.xml'

    def test_module_parameters_template(self):
        args = dict(
            name='fake_policy',
            state='present',
            template='LotusDomino 6.5 (http)'
        )

        p = V1Parameters(params=args)
        assert p.name == 'fake_policy'
        assert p.state == 'present'
        assert p.template == 'POLICY_TEMPLATE_LOTUSDOMINO_6_5_HTTP'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()
        self.policy = os.path.join(fixture_path, 'fake_policy.xml')
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_activate_import_from_file(self, *args):
        set_module_args(dict(
            name='fake_policy',
            file=self.policy,
            state='present',
            active='yes',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
        )

        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.import_to_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.read_current_from_device = Mock(return_value=current)
        v1.apply_on_device = Mock(return_value=True)
        v1.remove_temp_policy_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_policy'
        assert results['file'] == self.policy
        assert results['active'] is True

    def test_activate_import_from_template(self, *args):
        set_module_args(dict(
            name='fake_policy',
            template='OWA Exchange 2007 (https)',
            state='present',
            active='yes',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.import_to_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.read_current_from_device = Mock(return_value=current)
        v1.apply_on_device = Mock(return_value=True)
        v1.create_from_template_on_device = Mock(return_value=True)
        v1._file_is_missing = Mock(return_value=False)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_policy'
        assert results['template'] == 'OWA Exchange 2007 (https)'
        assert results['active'] is True

    def test_activate_create_by_name(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            active='yes',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.import_to_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.create_on_device = Mock(return_value=True)
        v1.create_blank = Mock(return_value=True)
        v1.read_current_from_device = Mock(return_value=current)
        v1.apply_on_device = Mock(return_value=True)
        v1._file_is_missing = Mock(return_value=False)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_policy'
        assert results['active'] is True

    def test_activate_policy_exists_inactive(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            active='yes',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=True)
        v1.update_on_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.read_current_from_device = Mock(return_value=current)
        v1.apply_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['active'] is True

    def test_activate_policy_exists_active(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            active='yes',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_active.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=True)
        v1.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_deactivate_policy_exists_active(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            server='localhost',
            password='password',
            user='admin',
            active='no'
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_active.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=True)
        v1.read_current_from_device = Mock(return_value=current)
        v1.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['active'] is False

    def test_deactivate_policy_exists_inactive(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            server='localhost',
            password='password',
            user='admin',
            active='no'
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=True)
        v1.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_import_from_file(self, *args):
        set_module_args(dict(
            name='fake_policy',
            file=self.policy,
            state='present',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.import_to_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.read_current_from_device = Mock(return_value=current)
        v1.remove_temp_policy_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_policy'
        assert results['file'] == self.policy
        assert results['active'] is False

    def test_import_from_template(self, *args):
        set_module_args(dict(
            name='fake_policy',
            template='LotusDomino 6.5 (http)',
            state='present',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.create_from_template_on_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.read_current_from_device = Mock(return_value=current)
        v1._file_is_missing = Mock(return_value=False)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_policy'
        assert results['template'] == 'LotusDomino 6.5 (http)'
        assert results['active'] is False

    def test_create_by_name(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.import_to_device = Mock(return_value=True)
        v1.wait_for_task = Mock(side_effect=[True, True])
        v1.create_on_device = Mock(return_value=True)
        v1.create_blank = Mock(return_value=True)
        v1.read_current_from_device = Mock(return_value=current)
        v1.apply_on_device = Mock(return_value=True)
        v1._file_is_missing = Mock(return_value=False)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'fake_policy'
        assert results['active'] is False

    def test_delete_policy(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='absent',
            server='localhost',
            password='password',
            user='admin',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(side_effect=[True, False])
        v1.remove_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_policy_import_raises(self, *args):
        set_module_args(dict(
            name='fake_policy',
            file=self.policy,
            state='present',
            server='localhost',
            password='password',
            user='admin',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        msg = 'Import policy task failed.'
        # Override methods to force specific logic in the module to happen
        v2 = V2Manager(module=module)
        v2.exists = Mock(return_value=False)
        v2.import_to_device = Mock(return_value=True)
        v2.wait_for_task = Mock(return_value=False)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v2)

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg

    def test_activate_policy_raises(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            active='yes',
            server='localhost',
            password='password',
            user='admin',
        ))

        current = V1Parameters(params=load_fixture('load_asm_policy_inactive.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        msg = 'Apply policy task failed.'
        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=True)
        v1.wait_for_task = Mock(return_value=False)
        v1.update_on_device = Mock(return_value=True)
        v1.read_current_from_device = Mock(return_value=current)
        v1.apply_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg

    def test_create_policy_raises(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='present',
            server='localhost',
            password='password',
            user='admin',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        msg = 'Failed to create ASM policy: fake_policy'
        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(return_value=False)
        v1.create_on_device = Mock(return_value=False)
        v1._file_is_missing = Mock(return_value=False)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg

    def test_delete_policy_raises(self, *args):
        set_module_args(dict(
            name='fake_policy',
            state='absent',
            server='localhost',
            password='password',
            user='admin',
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        msg = 'Failed to delete ASM policy: fake_policy'
        # Override methods to force specific logic in the module to happen
        v1 = V1Manager(module=module)
        v1.exists = Mock(side_effect=[True, True])
        v1.remove_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_13 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=v1)

        with pytest.raises(F5ModuleError) as err:
            mm.exec_module()
        assert str(err.value) == msg
