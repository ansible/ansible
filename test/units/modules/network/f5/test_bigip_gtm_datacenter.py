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
    from library.modules.bigip_gtm_datacenter import ApiParameters
    from library.modules.bigip_gtm_datacenter import ModuleParameters
    from library.modules.bigip_gtm_datacenter import ModuleManager
    from library.modules.bigip_gtm_datacenter import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_gtm_datacenter import ApiParameters
    from ansible.modules.network.f5.bigip_gtm_datacenter import ModuleParameters
    from ansible.modules.network.f5.bigip_gtm_datacenter import ModuleManager
    from ansible.modules.network.f5.bigip_gtm_datacenter import ArgumentSpec

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
            state='present',
            contact='foo',
            description='bar',
            location='baz',
            name='datacenter'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'present'

    def test_api_parameters(self):
        args = load_fixture('load_gtm_datacenter_default.json')
        p = ApiParameters(params=args)
        assert p.name == 'asd'

    def test_module_parameters_state_present(self):
        args = dict(
            state='present'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'present'
        assert p.enabled is True

    def test_module_parameters_state_absent(self):
        args = dict(
            state='absent'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'absent'

    def test_module_parameters_state_enabled(self):
        args = dict(
            state='enabled'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'enabled'
        assert p.enabled is True
        assert p.disabled is None

    def test_module_parameters_state_disabled(self):
        args = dict(
            state='disabled'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'disabled'
        assert p.enabled is None
        assert p.disabled is True


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

        try:
            self.p1 = patch('library.modules.bigip_gtm_datacenter.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True
        except Exception:
            self.p1 = patch('ansible.modules.network.f5.bigip_gtm_datacenter.module_provisioned')
            self.m1 = self.p1.start()
            self.m1.return_value = True

    def tearDown(self):
        self.p1.stop()

    def test_create_datacenter(self, *args):
        set_module_args(dict(
            name='foo',
            state='present',
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
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['state'] == 'present'

    def test_create_disabled_datacenter(self, *args):
        set_module_args(dict(
            name='foo',
            state='disabled',
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
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['enabled'] is False
        assert results['disabled'] is True

    def test_create_enabled_datacenter(self, *args):
        set_module_args(dict(
            name='foo',
            state='enabled',
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
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['enabled'] is True
        assert results['disabled'] is False

    def test_idempotent_disable_datacenter(self, *args):
        set_module_args(dict(
            name='foo',
            state='disabled',
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

        current = ApiParameters(params=load_fixture('load_gtm_datacenter_disabled.json'))

        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.module_provisioned = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is False
