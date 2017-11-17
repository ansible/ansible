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
from ansible.module_utils.f5_utils import AnsibleF5Client
from units.modules.utils import set_module_args

try:
    from library.bigip_policy import Parameters
    from library.bigip_policy import ModuleManager
    from library.bigip_policy import SimpleManager
    from library.bigip_policy import ComplexManager
    from library.bigip_policy import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_policy import Parameters
        from ansible.modules.network.f5.bigip_policy import ModuleManager
        from ansible.modules.network.f5.bigip_policy import SimpleManager
        from ansible.modules.network.f5.bigip_policy import ComplexManager
        from ansible.modules.network.f5.bigip_policy import ArgumentSpec
        from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
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
    def test_module_parameters_none_strategy(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            password='password',
            server='localhost',
            user='admin'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy is None

    def test_module_parameters_with_strategy_no_partition(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            password='password',
            server='localhost',
            strategy='foo',
            user='admin',
            partition='Common'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Common/foo'

    def test_module_parameters_with_strategy_partition(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            password='password',
            server='localhost',
            strategy='/Common/foo',
            user='admin',
            partition='Common'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Common/foo'

    def test_module_parameters_with_strategy_different_partition(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            password='password',
            server='localhost',
            strategy='/Foo/bar',
            user='admin',
            partition='Common'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Foo/bar'

    def test_api_parameters(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            strategy='/Common/asdf'
        )
        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Common/asdf'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestSimpleTrafficPolicyManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_policy(self, *args):
        set_module_args(dict(
            name="Policy-Foo",
            state='present',
            strategy='best',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        tm = SimpleManager(client)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
