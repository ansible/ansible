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
    from library.modules.bigip_policy import Parameters
    from library.modules.bigip_policy import ModuleManager
    from library.modules.bigip_policy import SimpleManager
    from library.modules.bigip_policy import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_policy import Parameters
    from ansible.modules.network.f5.bigip_policy import ModuleManager
    from ansible.modules.network.f5.bigip_policy import SimpleManager
    from ansible.modules.network.f5.bigip_policy import ArgumentSpec

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
    def test_module_parameters_none_strategy(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
        )
        p = Parameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy is None

    def test_module_parameters_with_strategy_no_partition(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            strategy='foo',
            partition='Common'
        )
        p = Parameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Common/foo'

    def test_module_parameters_with_strategy_partition(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            strategy='/Common/foo',
            partition='Common'
        )
        p = Parameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Common/foo'

    def test_module_parameters_with_strategy_different_partition(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            strategy='/Foo/bar',
            partition='Common'
        )
        p = Parameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Foo/bar'

    def test_api_parameters(self):
        args = dict(
            name='foo',
            description='asdf asdf asdf',
            strategy='/Common/asdf'
        )
        p = Parameters(params=args)
        assert p.name == 'foo'
        assert p.description == 'asdf asdf asdf'
        assert p.strategy == '/Common/asdf'


class TestSimpleTrafficPolicyManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_policy(self, *args):
        set_module_args(dict(
            name="Policy-Foo",
            state='present',
            strategy='best',
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
        tm = SimpleManager(module=module, params=module.params)
        tm.exists = Mock(return_value=False)
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.version_is_less_than_12 = Mock(return_value=True)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
