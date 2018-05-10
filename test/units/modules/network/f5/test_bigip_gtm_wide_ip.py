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
    from library.modules.bigip_gtm_wide_ip import ApiParameters
    from library.modules.bigip_gtm_wide_ip import ModuleParameters
    from library.modules.bigip_gtm_wide_ip import ModuleManager
    from library.modules.bigip_gtm_wide_ip import ArgumentSpec
    from library.modules.bigip_gtm_wide_ip import UntypedManager
    from library.modules.bigip_gtm_wide_ip import TypedManager
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_wide_ip import ApiParameters
        from ansible.modules.network.f5.bigip_gtm_wide_ip import ModuleParameters
        from ansible.modules.network.f5.bigip_gtm_wide_ip import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_wide_ip import ArgumentSpec
        from ansible.modules.network.f5.bigip_gtm_wide_ip import UntypedManager
        from ansible.modules.network.f5.bigip_gtm_wide_ip import TypedManager
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
            name='foo.baz.bar',
            pool_lb_method='round-robin',
        )
        p = ModuleParameters(params=args)
        assert p.name == 'foo.baz.bar'
        assert p.pool_lb_method == 'round-robin'

    def test_module_pools(self):
        args = dict(
            pools=[
                dict(
                    name='foo',
                    ratio='100'
                )
            ]
        )
        p = ModuleParameters(params=args)
        assert len(p.pools) == 1

    def test_api_parameters(self):
        args = dict(
            name='foo.baz.bar',
            poolLbMode='round-robin'
        )
        p = ApiParameters(params=args)
        assert p.name == 'foo.baz.bar'
        assert p.pool_lb_method == 'round-robin'

    def test_api_pools(self):
        args = load_fixture('load_gtm_wide_ip_with_pools.json')
        p = ApiParameters(params=args)
        assert len(p.pools) == 1
        assert 'name' in p.pools[0]
        assert 'ratio' in p.pools[0]
        assert p.pools[0]['name'] == '/Common/baz'
        assert p.pools[0]['ratio'] == 10

    def test_module_not_fqdn_name(self):
        args = dict(
            name='foo',
            lb_method='round-robin'
        )
        with pytest.raises(F5ModuleError) as excinfo:
            p = ModuleParameters(params=args)
            assert p.name == 'foo'
        assert 'The provided name must be a valid FQDN' in str(excinfo)


class TestUntypedManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_wideip(self, *args):
        set_module_args(dict(
            name='foo.baz.bar',
            lb_method='round-robin',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = UntypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'foo.baz.bar'
        assert results['state'] == 'present'
        assert results['lb_method'] == 'round-robin'


class TestTypedManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_wideip(self, *args):
        set_module_args(dict(
            name='foo.baz.bar',
            lb_method='round-robin',
            type='a',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'foo.baz.bar'
        assert results['state'] == 'present'
        assert results['lb_method'] == 'round-robin'

    def test_create_wideip_deprecated_lb_method1(self, *args):
        set_module_args(dict(
            name='foo.baz.bar',
            lb_method='round_robin',
            type='a',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'foo.baz.bar'
        assert results['state'] == 'present'
        assert results['lb_method'] == 'round-robin'

    def test_create_wideip_deprecated_lb_method2(self, *args):
        set_module_args(dict(
            name='foo.baz.bar',
            lb_method='global_availability',
            type='a',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'foo.baz.bar'
        assert results['state'] == 'present'
        assert results['lb_method'] == 'global-availability'

    def test_create_wideip_with_pool(self, *args):
        set_module_args(dict(
            name='foo.baz.bar',
            lb_method='round-robin',
            type='a',
            pools=[
                dict(
                    name='foo',
                    ratio=10
                )
            ],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['name'] == 'foo.baz.bar'
        assert results['state'] == 'present'
        assert results['lb_method'] == 'round-robin'

    def test_create_wideip_with_pool_idempotent(self, *args):
        set_module_args(dict(
            name='foo.bar.com',
            lb_method='round-robin',
            type='a',
            pools=[
                dict(
                    name='baz',
                    ratio=10
                )
            ],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = ApiParameters(params=load_fixture('load_gtm_wide_ip_with_pools.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_wideip_with_pool(self, *args):
        set_module_args(dict(
            name='foo.bar.com',
            lb_method='round-robin',
            type='a',
            pools=[
                dict(
                    name='baz',
                    ratio=10
                ),
                dict(
                    name='alec',
                    ratio=100
                )
            ],
            password='passsword',
            server='localhost',
            user='admin'
        ))

        current = ApiParameters(params=load_fixture('load_gtm_wide_ip_with_pools.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module, params=module.params)
        tm.exists = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)
        tm.update_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert 'pools' in results
