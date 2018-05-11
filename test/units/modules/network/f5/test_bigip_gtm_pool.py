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
    from library.modules.bigip_gtm_pool import ApiParameters
    from library.modules.bigip_gtm_pool import ModuleParameters
    from library.modules.bigip_gtm_pool import ModuleManager
    from library.modules.bigip_gtm_pool import ArgumentSpec
    from library.modules.bigip_gtm_pool import UntypedManager
    from library.modules.bigip_gtm_pool import TypedManager
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_pool import ApiParameters
        from ansible.modules.network.f5.bigip_gtm_pool import ModuleParameters
        from ansible.modules.network.f5.bigip_gtm_pool import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_pool import ArgumentSpec
        from ansible.modules.network.f5.bigip_gtm_pool import UntypedManager
        from ansible.modules.network.f5.bigip_gtm_pool import TypedManager
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
            name='foo',
            preferred_lb_method='topology',
            alternate_lb_method='ratio',
            fallback_lb_method='fewest-hops',
            fallback_ip='10.10.10.10',
            type='a'
        )
        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.preferred_lb_method == 'topology'
        assert p.alternate_lb_method == 'ratio'
        assert p.fallback_lb_method == 'fewest-hops'
        assert p.fallback_ip == '10.10.10.10'
        assert p.type == 'a'

    def test_module_parameters_members(self):
        args = dict(
            partition='Common',
            members=[
                dict(
                    server='foo',
                    virtual_server='bar'
                )
            ]
        )
        p = ModuleParameters(params=args)
        assert len(p.members) == 1
        assert p.members[0] == '/Common/foo:bar'

    def test_api_parameters(self):
        args = dict(
            name='foo',
            loadBalancingMode='topology',
            alternateMode='ratio',
            fallbackMode='fewest-hops',
            fallbackIp='10.10.10.10'
        )
        p = ApiParameters(params=args)
        assert p.name == 'foo'
        assert p.preferred_lb_method == 'topology'
        assert p.alternate_lb_method == 'ratio'
        assert p.fallback_lb_method == 'fewest-hops'
        assert p.fallback_ip == '10.10.10.10'

    def test_api_parameters_members(self):
        args = load_fixture('load_gtm_pool_a_with_members_1.json')
        p = ApiParameters(params=args)
        assert len(p.members) == 3
        assert p.members[0] == '/Common/server1:vs1'
        assert p.members[1] == '/Common/server1:vs2'
        assert p.members[2] == '/Common/server1:vs3'


class TestUntypedManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_pool(self, *args):
        set_module_args(dict(
            name='foo',
            preferred_lb_method='round-robin',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = UntypedManager(module=module)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['preferred_lb_method'] == 'round-robin'

    def test_update_pool(self, *args):
        set_module_args(dict(
            name='foo',
            preferred_lb_method='topology',
            alternate_lb_method='drop-packet',
            fallback_lb_method='cpu',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        current = ApiParameters(params=load_fixture('load_gtm_pool_untyped_default.json'))

        # Override methods in the specific type of manager
        tm = UntypedManager(module=module)
        tm.exists = Mock(side_effect=[True, True])
        tm.update_on_device = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['preferred_lb_method'] == 'topology'
        assert results['alternate_lb_method'] == 'drop-packet'
        assert results['fallback_lb_method'] == 'cpu'

    def test_delete_pool(self, *args):
        set_module_args(dict(
            name='foo',
            state='absent',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = UntypedManager(module=module)
        tm.exists = Mock(side_effect=[True, False])
        tm.remove_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True


class TestTypedManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_pool(self, *args):
        set_module_args(dict(
            name='foo',
            preferred_lb_method='round-robin',
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
        tm = TypedManager(module=module)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['preferred_lb_method'] == 'round-robin'

    def test_update_pool(self, *args):
        set_module_args(dict(
            name='foo',
            preferred_lb_method='topology',
            alternate_lb_method='drop-packet',
            fallback_lb_method='cpu',
            type='a',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        current = ApiParameters(params=load_fixture('load_gtm_pool_a_default.json'))

        # Override methods in the specific type of manager
        tm = TypedManager(module=module)
        tm.exists = Mock(side_effect=[True, True])
        tm.update_on_device = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['preferred_lb_method'] == 'topology'
        assert results['alternate_lb_method'] == 'drop-packet'
        assert results['fallback_lb_method'] == 'cpu'

    def test_delete_pool(self, *args):
        set_module_args(dict(
            name='foo',
            type='a',
            state='absent',
            password='passsword',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        tm = TypedManager(module=module)
        tm.exists = Mock(side_effect=[True, False])
        tm.remove_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
