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
    from library.modules.bigip_pool_member import ModuleParameters
    from library.modules.bigip_pool_member import ApiParameters
    from library.modules.bigip_pool_member import NodeApiParameters
    from library.modules.bigip_pool_member import ModuleManager
    from library.modules.bigip_pool_member import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_pool_member import ModuleParameters
    from ansible.modules.network.f5.bigip_pool_member import ApiParameters
    from ansible.modules.network.f5.bigip_pool_member import NodeApiParameters
    from ansible.modules.network.f5.bigip_pool_member import ModuleManager
    from ansible.modules.network.f5.bigip_pool_member import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock

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
            pool='my-pool',
            address='1.2.3.4',
            fqdn='fqdn.foo.bar',
            name='my-name',
            port=2345,
            connection_limit=100,
            description='this is a description',
            rate_limit=70,
            ratio=20,
            preserve_node=False,
            priority_group=10,
            state='present',
            partition='Common',
            fqdn_auto_populate=False,
            reuse_nodes=False,
        )

        p = ModuleParameters(params=args)
        assert p.name == 'my-name'

    def test_api_parameters(self):
        args = load_fixture('load_net_node_with_fqdn.json')
        p = ApiParameters(params=args)
        assert p.state == 'present'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_reuse_node_with_name(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            fqdn='foo.bar.com',
            port=2345,
            state='present',
            partition='Common',
            reuse_nodes=True,
            provider=dict(
                password='password',
                server='localhost',
                user='admin'
            )
        ))

        current_node = NodeApiParameters(params=load_fixture('load_net_node_with_fqdn.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of,
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.read_current_node_from_device = Mock(return_value=current_node)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is True
        assert results['fqdn'] == 'foo.bar.com'
        assert results['state'] == 'present'

    def test_create_reuse_node_with_ipv4_address(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            address='7.3.67.8',
            port=2345,
            state='present',
            partition='Common',
            reuse_nodes=True,
            provider=dict(
                password='password',
                server='localhost',
                user='admin'
            )
        ))

        current_node = NodeApiParameters(params=load_fixture('load_net_node_with_ipv4_address.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of,
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.read_current_node_from_device = Mock(return_value=current_node)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is False
        assert results['address'] == '7.3.67.8'
        assert results['state'] == 'present'

    def test_create_reuse_node_with_fqdn_auto_populate(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            fqdn='foo.bar.com',
            port=2345,
            state='present',
            partition='Common',
            reuse_nodes=True,
            fqdn_auto_populate=False,
            provider=dict(
                password='password',
                server='localhost',
                user='admin'
            )
        ))

        current_node = NodeApiParameters(params=load_fixture('load_net_node_with_fqdn.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of,
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.read_current_node_from_device = Mock(return_value=current_node)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is True
        assert results['fqdn'] == 'foo.bar.com'
        assert results['state'] == 'present'

    def test_create_aggregate_pool_members(self, *args):
        set_module_args(dict(
            pool='fake_pool',
            aggregate=[
                dict(
                    name='my-name',
                    host="1.1.1.1",
                    port=1234,
                    state='present',
                    partition='Common',
                    reuse_nodes=True,
                    fqdn_auto_populate=False,
                ),
                dict(
                    name='my-name2',
                    fqdn='google.com',
                    port=2423,
                    state='present',
                    partition='Common',
                    fqdn_auto_populate=True,
                    reuse_nodes=True,
                )
            ],
            provider=dict(
                password='password',
                server='localhost',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
            required_one_of=self.spec.required_one_of,
        )

        mm = ModuleManager(module=module)
        mm.create_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
