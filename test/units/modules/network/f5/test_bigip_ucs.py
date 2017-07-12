# -*- coding: utf-8 -*-
#
# Copyright 2017 F5 Networks Inc.
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
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import F5ModuleError

try:
    from library.bigip_ucs import Parameters
    from library.bigip_ucs import ModuleManager
    from library.bigip_ucs import ArgumentSpec
    from library.bigip_ucs import V1Manager
    from library.bigip_ucs import V2Manager
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_ucs import Parameters
        from ansible.modules.network.f5.bigip_ucs import ModuleManager
        from ansible.modules.network.f5.bigip_ucs import ArgumentSpec
        from ansible.modules.network.f5.bigip_ucs import V1Manager
        from ansible.modules.network.f5.bigip_ucs import V2Manager
    except ImportError:
        raise SkipTest("F5 Ansible modules require the f5-sdk Python library")

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


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

        p = Parameters(args)
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

        p = Parameters(args)
        assert p.ucs == '/root/bigip.localhost.localdomain.ucs'
        assert p.include_chassis_level_config is False
        assert p.no_license is False
        assert p.no_platform_check is False
        assert p.reset_trust is False
        assert p.install_command == "tmsh load sys ucs /var/local/ucs/bigip.localhost.localdomain.ucs"


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestV1Manager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_ucs_default_present(self, *args):
        set_module_args(dict(
            ucs="/root/bigip.localhost.localdomain.ucs",
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=True)

        vm = V1Manager(client)
        vm.remove_from_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[True, True])

        with pytest.raises(F5ModuleError) as ex:
            vm.exec_module()
        assert 'Failed to delete' in str(ex.value)


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V2Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V2Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V2Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V1Manager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_v1 = Mock(return_value=False)

        vm = V1Manager(client)
        vm.remove_from_device = Mock(return_value=True)
        vm.exists = Mock(side_effect=[True, True])

        with pytest.raises(F5ModuleError) as ex:
            vm.exec_module()
        assert 'Failed to delete' in str(ex.value)
