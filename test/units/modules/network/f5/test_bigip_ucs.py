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
    from library.modules.bigip_ucs import Parameters
    from library.modules.bigip_ucs import ModuleManager
    from library.modules.bigip_ucs import ArgumentSpec
    from library.modules.bigip_ucs import V1Manager
    from library.modules.bigip_ucs import V2Manager
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_ucs import Parameters
        from ansible.modules.network.f5.bigip_ucs import ModuleManager
        from ansible.modules.network.f5.bigip_ucs import ArgumentSpec
        from ansible.modules.network.f5.bigip_ucs import V1Manager
        from ansible.modules.network.f5.bigip_ucs import V2Manager
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
            ucs="/root/bigip.localhost.localdomain.ucs",
            force=True,
            include_chassis_level_config=True,
            no_license=True,
            no_platform_check=True,
            passphrase="foobar",
            reset_trust=True,
            state='installed'
        )

        p = Parameters(params=args)
        assert p.ucs == '/root/bigip.localhost.localdomain.ucs'
        assert p.force is True
        assert p.include_chassis_level_config is True
        assert p.no_license is True
        assert p.no_platform_check is True
        assert p.passphrase == "foobar"
        assert p.reset_trust is True
        assert p.install_command == \
            "tmsh load sys ucs /var/local/ucs/bigip.localhost.localdomain.ucs " \
            "include-chassis-level-config no-license no-platform-check " \
            "passphrase foobar reset-trust"

    def test_module_parameters_false_ucs_booleans(self):
        args = dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            include_chassis_level_config=False,
            no_license=False,
            no_platform_check=False,
            reset_trust=False
        )

        p = Parameters(params=args)
        assert p.ucs == '/root/bigip.localhost.localdomain.ucs'
        assert p.include_chassis_level_config is False
        assert p.no_license is False
        assert p.no_platform_check is False
        assert p.reset_trust is False
        assert p.install_command == "tmsh load sys ucs /var/local/ucs/bigip.localhost.localdomain.ucs"


class TestV1Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.patcher1 = patch('time.sleep')
        self.patcher1.start()

    def tearDown(self):
        self.patcher1.stop()

    def test_ucs_default_present(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(module=module)
        vm.create_on_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[False, True])

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_explicit_present(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='present'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(module=module)
        vm.create_on_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[False, True])

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_installed(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='installed'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(module=module)
        vm.create_on_device = Mock(return_value=True)
        vm.exists = Mock(return_value=True)
        vm.install_on_device = Mock(return_value=True)

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_absent_exists(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='absent'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(module=module)
        vm.remove_from_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[True, False])

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_absent_fails(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='absent'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(module=module)
        vm.remove_from_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[True, True])

        with pytest.raises(F5ModuleError) as ex:
            vm.exec_module()
        assert 'Failed to delete' in str(ex.value)


class TestV2Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_ucs_default_present(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V2Manager(module=module)
        vm.create_on_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[False, True])

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_explicit_present(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='present'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V2Manager(module=module)
        vm.create_on_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[False, True])

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_installed(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='installed'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V2Manager(module=module)
        vm.create_on_device = Mock(return_value=True)
        vm.exists = Mock(return_value=True)
        vm.install_on_device = Mock(return_value=True)

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_absent_exists(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='absent'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V1Manager(module=module)
        vm.remove_from_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[True, False])

        results = vm.exec_module()

        assert results['changed'] is True

    def test_ucs_absent_fails(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin',
            state='absent'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V1Manager(module=module)
        vm.remove_from_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[True, True])

        with pytest.raises(F5ModuleError) as ex:
            vm.exec_module()
        assert 'Failed to delete' in str(ex.value)
