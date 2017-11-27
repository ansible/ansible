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
# GNU General Public Liccense for more details.
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
    from library.bigip_partition import Parameters
    from library.bigip_partition import ModuleManager
    from library.bigip_partition import ArgumentSpec
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_partition import Parameters
        from ansible.modules.network.f5.bigip_partition import ModuleManager
        from ansible.modules.network.f5.bigip_partition import ArgumentSpec
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
    def test_module_parameters(self):
        args = dict(
            name='foo',
            description='my description',
            route_domain=0
        )

        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'my description'
        assert p.route_domain == 0

    def test_module_parameters_string_domain(self):
        args = dict(
            name='foo',
            route_domain='0'
        )

        p = Parameters(args)
        assert p.name == 'foo'
        assert p.route_domain == 0

    def test_api_parameters(self):
        args = dict(
            name='foo',
            description='my description',
            defaultRouteDomain=1
        )

        p = Parameters(args)
        assert p.name == 'foo'
        assert p.description == 'my description'
        assert p.route_domain == 1


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManagerEcho(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_partition(self, *args):
        set_module_args(dict(
            name='foo',
            description='my description',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_partition_idempotent(self, *args):
        set_module_args(dict(
            name='foo',
            description='my description',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = Parameters(load_fixture('load_tm_auth_partition.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_description(self, *args):
        set_module_args(dict(
            name='foo',
            description='another description',
            server='localhost',
            password='password',
            user='admin'
        ))

        current = Parameters(load_fixture('load_tm_auth_partition.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'another description'

    def test_update_route_domain(self, *args):
        set_module_args(dict(
            name='foo',
            route_domain=1,
            server='localhost',
            password='password',
            user='admin'
        ))

        current = Parameters(load_fixture('load_tm_auth_partition.json'))
        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(client)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['route_domain'] == 1
