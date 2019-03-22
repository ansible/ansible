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
from ansible.module_utils.six import PY3

try:
    from library.modules.bigip_irule import Parameters
    from library.modules.bigip_irule import ModuleManager
    from library.modules.bigip_irule import ArgumentSpec
    from library.modules.bigip_irule import GtmManager
    from library.modules.bigip_irule import LtmManager

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch
    from test.units.compat.mock import mock_open

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_irule import Parameters
    from ansible.modules.network.f5.bigip_irule import ModuleManager
    from ansible.modules.network.f5.bigip_irule import ArgumentSpec
    from ansible.modules.network.f5.bigip_irule import GtmManager
    from ansible.modules.network.f5.bigip_irule import LtmManager

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch
    from units.compat.mock import mock_open

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


class BigIpObj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestParameters(unittest.TestCase):
    def test_module_parameters_ltm(self):
        content = load_fixture('create_ltm_irule.tcl')
        args = dict(
            content=content,
            module='ltm',
            name='foo',
            state='present'
        )
        p = Parameters(params=args)
        assert p.content == content

    def test_module_parameters_gtm(self):
        content = load_fixture('create_gtm_irule.tcl')
        args = dict(
            content=content,
            module='gtm',
            name='foo',
            state='present'
        )
        p = Parameters(params=args)
        assert p.content == content

    def test_api_parameters_ltm(self):
        content = load_fixture('create_ltm_irule.tcl')
        args = dict(
            apiAnonymous=content
        )
        p = Parameters(params=args)
        assert p.content == content

    def test_return_api_params(self):
        content = load_fixture('create_ltm_irule.tcl')
        args = dict(
            content=content,
            module='ltm',
            name='foo',
            state='present'
        )
        p = Parameters(params=args)
        params = p.api_params()

        assert 'apiAnonymous' in params


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()
        self.ltm_irules = []
        self.gtm_irules = []

        members = load_fixture('load_ltm_irules.json')
        for item in members:
            self.ltm_irules.append(BigIpObj(**item))

        members = load_fixture('load_gtm_irules.json')
        for item in members:
            self.gtm_irules.append(BigIpObj(**item))

    def test_create_ltm_irule(self, *args):
        set_module_args(dict(
            name='foo',
            module='ltm',
            content='this is my content',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        tm = LtmManager(module=module, params=module.params)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['content'] == 'this is my content'

    def test_create_gtm_irule(self, *args):
        set_module_args(dict(
            name='foo',
            module='gtm',
            content='this is my content',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        tm = GtmManager(module=module, params=module.params)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(module=module)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['content'] == 'this is my content'

    def test_create_gtm_irule_src(self, *args):
        set_module_args(dict(
            name='foo',
            module='gtm',
            src='{0}/create_ltm_irule.tcl'.format(fixture_path),
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        if PY3:
            builtins_name = 'builtins'
        else:
            builtins_name = '__builtin__'

        with patch(builtins_name + '.open', mock_open(read_data='this is my content'), create=True):
            # Override methods in the specific type of manager
            tm = GtmManager(module=module, params=module.params)
            tm.exists = Mock(side_effect=[False, True])
            tm.create_on_device = Mock(return_value=True)

            # Override methods to force specific logic in the module to happen
            mm = ModuleManager(module=module)
            mm.get_manager = Mock(return_value=tm)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['content'] == 'this is my content'
        assert results['module'] == 'gtm'
        assert results['src'] == '{0}/create_ltm_irule.tcl'.format(fixture_path)
        assert len(results.keys()) == 4

    def test_module_mutual_exclusion(self, *args):
        set_module_args(dict(
            content='foo',
            module='ltm',
            name='foo',
            state='present',
            src='/path/to/irules/foo.tcl',
            partition='Common',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        with patch('ansible.module_utils.basic.AnsibleModule.fail_json', unsafe=True) as mo:
            AnsibleModule(
                argument_spec=self.spec.argument_spec,
                supports_check_mode=self.spec.supports_check_mode,
                mutually_exclusive=self.spec.mutually_exclusive,
            )
            mo.assert_called_once()
