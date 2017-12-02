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
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_gtm_datacenter import Parameters
    from library.bigip_gtm_datacenter import ModuleManager
    from library.bigip_gtm_datacenter import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_datacenter import Parameters
        from ansible.modules.network.f5.bigip_gtm_datacenter import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_datacenter import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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
            state='present',
            contact='foo',
            description='bar',
            location='baz',
            name='datacenter'
        )
        p = Parameters(args)
        assert p.state == 'present'

    def test_api_parameters(self):
        args = load_fixture('load_gtm_datacenter_default.json')
        p = Parameters(args)
        assert p.name == 'asd'

    def test_module_parameters_state_present(self):
        args = dict(
            state='present'
        )
        p = Parameters(args)
        assert p.state == 'present'
        assert p.enabled is True

    def test_module_parameters_state_absent(self):
        args = dict(
            state='absent'
        )
        p = Parameters(args)
        assert p.state == 'absent'

    def test_module_parameters_state_enabled(self):
        args = dict(
            state='enabled'
        )
        p = Parameters(args)
        assert p.state == 'enabled'
        assert p.enabled is True
        assert p.disabled is False

    def test_module_parameters_state_disabled(self):
        args = dict(
            state='disabled'
        )
        p = Parameters(args)
        assert p.state == 'disabled'
        assert p.enabled is False
        assert p.disabled is True


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_datacenter(self, *args):
        set_module_args(dict(
            state='present',
            password='admin',
            server='localhost',
            user='admin',
            name='foo'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True

    def test_create_disabled_datacenter(self, *args):
        set_module_args(dict(
            state='disabled',
            password='admin',
            server='localhost',
            user='admin',
            name='foo'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['enabled'] is False

    def test_create_enabled_datacenter(self, *args):
        set_module_args(dict(
            state='enabled',
            password='admin',
            server='localhost',
            user='admin',
            name='foo'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['enabled'] is True

    def test_idempotent_disable_datacenter(self, *args):
        set_module_args(dict(
            state='disabled',
            password='admin',
            server='localhost',
            user='admin',
            name='foo'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        current = Parameters(load_fixture('load_gtm_datacenter_disabled.json'))

        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()
        assert results['changed'] is False
        assert results['enabled'] is False


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestLegacyManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_legacy_disable_datacenter(self, *args):
        set_module_args(dict(
            state='present',
            enabled='no',
            password='admin',
            server='localhost',
            user='admin',
            name='foo'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['enabled'] is False

    def test_legacy_enable_datacenter(self, *args):
        set_module_args(dict(
            state='present',
            enabled='yes',
            password='admin',
            server='localhost',
            user='admin',
            name='foo'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['enabled'] is True
