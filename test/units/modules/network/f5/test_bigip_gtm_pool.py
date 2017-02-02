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
import sys

from nose.plugins.skip import SkipTest
if sys.version_info < (2, 7):
    raise SkipTest("F5 Ansible modules require Python >= 2.7")

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_gtm_pool import Parameters
    from library.bigip_gtm_pool import ModuleManager
    from library.bigip_gtm_pool import ArgumentSpec
    from library.bigip_gtm_pool import UntypedManager
    from library.bigip_gtm_pool import TypedManager
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_gtm_pool import Parameters
        from ansible.modules.network.f5.bigip_gtm_pool import ModuleManager
        from ansible.modules.network.f5.bigip_gtm_pool import ArgumentSpec
        from ansible.modules.network.f5.bigip_gtm_pool import UntypedManager
        from ansible.modules.network.f5.bigip_gtm_pool import TypedManager
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
            name='foo',
            preferred_lb_method='topology',
            alternate_lb_method='ratio',
            fallback_lb_method='fewest-hops',
            fallback_ip='10.10.10.10',
            type='a'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.preferred_lb_method == 'topology'
        assert p.alternate_lb_method == 'ratio'
        assert p.fallback_lb_method == 'fewest-hops'
        assert p.fallback_ip == '10.10.10.10'
        assert p.type == 'a'

    def test_api_parameters(self):
        args = dict(
            name='foo',
            loadBalancingMode='topology',
            alternateMode='ratio',
            fallbackMode='fewest-hops',
            fallbackIp='10.10.10.10'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.preferred_lb_method == 'topology'
        assert p.alternate_lb_method == 'ratio'
        assert p.fallback_lb_method == 'fewest-hops'
        assert p.fallback_ip == '10.10.10.10'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = UntypedManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        current = Parameters(load_fixture('load_gtm_pool_untyped_default.json'))

        # Override methods in the specific type of manager
        tm = UntypedManager(client)
        tm.exists = Mock(side_effect=[True, True])
        tm.update_on_device = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = UntypedManager(client)
        tm.exists = Mock(side_effect=[True, False])
        tm.remove_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TypedManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        current = Parameters(load_fixture('load_gtm_pool_a_default.json'))

        # Override methods in the specific type of manager
        tm = TypedManager(client)
        tm.exists = Mock(side_effect=[True, True])
        tm.update_on_device = Mock(return_value=True)
        tm.read_current_from_device = Mock(return_value=current)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
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

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = TypedManager(client)
        tm.exists = Mock(side_effect=[True, False])
        tm.remove_from_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.version_is_less_than_12 = Mock(return_value=False)
        mm.get_manager = Mock(return_value=tm)
        mm.gtm_provisioned = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
