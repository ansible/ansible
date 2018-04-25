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
    from library.modules.bigip_pool_member import ModuleParameters
    from library.modules.bigip_pool_member import ApiParameters
    from library.modules.bigip_pool_member import NodeApiParameters
    from library.modules.bigip_pool_member import ModuleManager
    from library.modules.bigip_pool_member import ArgumentSpec
    from library.module_utils.network.f5.common import F5ModuleError
    from library.module_utils.network.f5.common import iControlUnexpectedHTTPError
    from test.unit.modules.utils import set_module_args
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_pool_member import ModuleParameters
        from ansible.modules.network.f5.bigip_pool_member import ApiParameters
        from ansible.modules.network.f5.bigip_pool_member import NodeApiParameters
        from ansible.modules.network.f5.bigip_pool_member import ModuleManager
        from ansible.modules.network.f5.bigip_pool_member import ArgumentSpec
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

            # Deprecated params
            # TODO(Remove in 2.7)
            session_state='disabled',
            monitor_state='disabled',
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
            name='my-name',
            port=2345,
            state='present',
            partition='Common',
            reuse_nodes=True,
            password='password',
            server='localhost',
            user='admin'
        ))

        current_node = NodeApiParameters(params=load_fixture('load_net_node_with_fqdn.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
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
            name='7.3.67.8',
            port=2345,
            state='present',
            partition='Common',
            reuse_nodes=True,
            password='password',
            server='localhost',
            user='admin'
        ))

        current_node = NodeApiParameters(params=load_fixture('load_net_node_with_ipv4_address.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
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
            name='my-name',
            port=2345,
            state='present',
            partition='Common',
            reuse_nodes=True,
            fqdn_auto_populate=False,
            password='password',
            server='localhost',
            user='admin'
        ))

        current_node = NodeApiParameters(params=load_fixture('load_net_node_with_fqdn.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
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


class TestLegacyManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_name_is_hostname_with_session_and_monitor_enabled(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            name='my-name',
            port=2345,
            state='present',
            session_state='enabled',
            monitor_state='enabled',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is False
        assert results['fqdn'] == 'my-name'
        assert results['state'] == 'present'

    def test_create_name_is_address_with_session_and_monitor_enabled(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            name='10.10.10.10',
            port=2345,
            state='present',
            session_state='enabled',
            monitor_state='enabled',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is False
        assert results['address'] == '10.10.10.10'
        assert results['state'] == 'present'

    def test_create_name_is_address_with_session_disabled_and_monitor_enabled(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            name='10.10.10.10',
            port=2345,
            state='present',
            monitor_state='enabled',
            session_state='disabled',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is False
        assert results['address'] == '10.10.10.10'
        assert results['state'] == 'disabled'

    def test_create_name_is_address_with_session_and_monitor_disabled(self, *args):
        # Configure the arguments that would be sent to the Ansible module
        set_module_args(dict(
            pool='my-pool',
            name='10.10.10.10',
            port=2345,
            state='present',
            monitor_state='disabled',
            session_state='disabled',
            partition='Common',
            password='password',
            server='localhost',
            user='admin'
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['fqdn_auto_populate'] is False
        assert results['address'] == '10.10.10.10'
        assert results['state'] == 'forced_offline'
