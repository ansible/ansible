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
    from library.modules.bigip_partition import ApiParameters
    from library.modules.bigip_partition import ModuleParameters
    from library.modules.bigip_partition import ModuleManager
    from library.modules.bigip_partition import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_partition import ApiParameters
    from ansible.modules.network.f5.bigip_partition import ModuleParameters
    from ansible.modules.network.f5.bigip_partition import ModuleManager
    from ansible.modules.network.f5.bigip_partition import ArgumentSpec

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
            name='foo',
            description='my description',
            route_domain=0
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'my description'
        assert p.route_domain == 0

    def test_module_parameters_string_domain(self):
        args = dict(
            name='foo',
            route_domain='0'
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.route_domain == 0

    def test_api_parameters(self):
        args = dict(
            name='foo',
            description='my description',
            defaultRouteDomain=1
        )

        p = ApiParameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'my description'
        assert p.route_domain == 1


class TestManagerEcho(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_partition(self, *args):
        set_module_args(dict(
            name='foo',
            description='my description',
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

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)
        mm.update_folder_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_partition_idempotent(self, *args):
        set_module_args(dict(
            name='foo',
            description='my description',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_tm_auth_partition.json'))
        current.update({'folder_description': 'my description'})
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False

    def test_update_description(self, *args):
        set_module_args(dict(
            name='foo',
            description='another description',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_tm_auth_partition.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)
        mm.update_folder_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'another description'

    def test_update_route_domain(self, *args):
        set_module_args(dict(
            name='foo',
            route_domain=1,
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_tm_auth_partition.json'))
        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['route_domain'] == 1
