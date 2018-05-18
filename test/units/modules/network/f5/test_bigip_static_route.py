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
    from library.modules.bigip_static_route import ApiParameters
    from library.modules.bigip_static_route import ModuleParameters
    from library.modules.bigip_static_route import ModuleManager
    from library.modules.bigip_static_route import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_static_route import ApiParameters
        from ansible.modules.network.f5.bigip_static_route import ModuleParameters
        from ansible.modules.network.f5.bigip_static_route import ModuleManager
        from ansible.modules.network.f5.bigip_static_route import ArgumentSpec
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
            vlan="foo",
            gateway_address="10.10.10.10"
        )
        p = ModuleParameters(params=args)
        assert p.vlan == '/Common/foo'
        assert p.gateway_address == '10.10.10.10'

    def test_api_parameters(self):
        args = dict(
            tmInterface="foo",
            gw="10.10.10.10"
        )
        p = ApiParameters(params=args)
        assert p.vlan == 'foo'
        assert p.gateway_address == '10.10.10.10'

    def test_reject_parameter_types(self):
        # boolean true
        args = dict(reject=True)
        p = ModuleParameters(params=args)
        assert p.reject is True

        # boolean false
        args = dict(reject=False)
        p = ModuleParameters(params=args)
        assert p.reject is None

        # string
        args = dict(reject="yes")
        p = ModuleParameters(params=args)
        assert p.reject is True

        # integer
        args = dict(reject=1)
        p = ModuleParameters(params=args)
        assert p.reject is True

        # none
        args = dict(reject=None)
        p = ModuleParameters(params=args)
        assert p.reject is None

    def test_destination_parameter_types(self):
        # cidr address
        args = dict(
            destination="10.10.10.10",
            netmask='32'
        )
        p = ModuleParameters(params=args)
        assert p.destination == '10.10.10.10/32'

        # netmask
        args = dict(
            destination="10.10.10.10",
            netmask="255.255.255.255"
        )
        p = ModuleParameters(params=args)
        assert p.destination == '10.10.10.10/32'

    def test_vlan_with_partition(self):
        args = dict(
            vlan="/Common/foo",
            gateway_address="10.10.10.10"
        )
        p = ModuleParameters(params=args)
        assert p.vlan == '/Common/foo'
        assert p.gateway_address == '10.10.10.10'

    def test_api_route_domain(self):
        args = dict(
            destination="1.1.1.1/32%2"
        )
        p = ApiParameters(params=args)
        assert p.route_domain == 2

        args = dict(
            destination="2700:bc00:1f10:101::6/64%2"
        )
        p = ApiParameters(params=args)
        assert p.route_domain == 2


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_blackhole(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            destination='10.10.10.10',
            netmask='255.255.255.255',
            reject='yes'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True

    def test_create_route_to_pool(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            destination='10.10.10.10',
            netmask='255.255.255.255',
            pool="test-pool"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['pool'] == 'test-pool'

    def test_create_route_to_vlan(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            destination='10.10.10.10',
            netmask='255.255.255.255',
            vlan="test-vlan"
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['vlan'] == '/Common/test-vlan'

    def test_update_description(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            description='foo description'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        current = ApiParameters(params=load_fixture('load_net_route_description.json'))
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'foo description'

    def test_update_description_idempotent(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            description='asdasd'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        current = ApiParameters(params=load_fixture('load_net_route_description.json'))
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        results = mm.exec_module()

        # There is no assert for the description, because it should
        # not have changed
        assert results['changed'] is False

    def test_delete(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='absent'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, False])
        mm.remove_from_device = Mock(return_value=True)
        results = mm.exec_module()

        assert results['changed'] is True
        assert 'description' not in results

    def test_invalid_unknown_params(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            foo="bar"
        ))
        with patch('ansible.module_utils.f5_utils.AnsibleModule.fail_json') as mo:
            mo.return_value = True
            AnsibleModule(
                argument_spec=self.spec.argument_spec,
                mutually_exclusive=self.spec.mutually_exclusive,
                supports_check_mode=self.spec.supports_check_mode
            )
            assert mo.call_count == 1

    def test_create_with_route_domain(self, *args):
        set_module_args(dict(
            name='test-route',
            password='admin',
            server='localhost',
            user='admin',
            state='present',
            destination='10.10.10.10',
            netmask='255.255.255.255',
            route_domain=1,
            reject='yes'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            mutually_exclusive=self.spec.mutually_exclusive,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
        assert results['route_domain'] == 1
        assert results['destination'] == '10.10.10.10%1/32'
