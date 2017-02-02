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
from ansible.compat.tests.mock import patch, mock_open, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.six import PY3

try:
    from library.bigip_irule import Parameters
    from library.bigip_irule import ModuleManager
    from library.bigip_irule import ArgumentSpec
    from library.bigip_irule import GtmManager
    from library.bigip_irule import LtmManager
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_irule import Parameters
        from ansible.modules.network.f5.bigip_irule import ModuleManager
        from ansible.modules.network.f5.bigip_irule import ArgumentSpec
        from ansible.modules.network.f5.bigip_irule import GtmManager
        from ansible.modules.network.f5.bigip_irule import LtmManager
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
        p = Parameters(args)
        assert p.content == content.strip()

    def test_module_parameters_gtm(self):
        content = load_fixture('create_gtm_irule.tcl')
        args = dict(
            content=content,
            module='gtm',
            name='foo',
            state='present'
        )
        p = Parameters(args)
        assert p.content == content.strip()

    def test_api_parameters_ltm(self):
        content = load_fixture('create_ltm_irule.tcl')
        args = dict(
            apiAnonymous=content
        )
        p = Parameters(args)
        assert p.content == content.strip()

    def test_return_api_params(self):
        content = load_fixture('create_ltm_irule.tcl')
        args = dict(
            content=content,
            module='ltm',
            name='foo',
            state='present'
        )
        p = Parameters(args)
        params = p.api_params()

        assert 'apiAnonymous' in params


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
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
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        tm = LtmManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
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
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        # Override methods in the specific type of manager
        tm = GtmManager(client)
        tm.exists = Mock(side_effect=[False, True])
        tm.create_on_device = Mock(return_value=True)

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.get_manager = Mock(return_value=tm)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['content'] == 'this is my content'

    def test_create_gtm_irule_src(self, *args):
        set_module_args(dict(
            name='foo',
            module='gtm',
            src='/path/to/irules/foo.tcl',
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name,
            mutually_exclusive=self.spec.mutually_exclusive,
        )

        if PY3:
            builtins_name = 'builtins'
        else:
            builtins_name = '__builtin__'

        with patch(builtins_name + '.open', mock_open(read_data='this is my content'), create=True):
            # Override methods in the specific type of manager
            tm = GtmManager(client)
            tm.exists = Mock(side_effect=[False, True])
            tm.create_on_device = Mock(return_value=True)

            # Override methods to force specific logic in the module to happen
            mm = ModuleManager(client)
            mm.get_manager = Mock(return_value=tm)

            results = mm.exec_module()

        assert results['changed'] is True
        assert results['content'] == 'this is my content'
        assert results['module'] == 'gtm'
        assert results['src'] == '/path/to/irules/foo.tcl'
        assert len(results.keys()) == 4

    def test_module_mutual_exclusion(self, *args):
        set_module_args(dict(
            content='foo',
            module='ltm',
            name='foo',
            state='present',
            src='/path/to/irules/foo.tcl',
            partition='Common',
            server='localhost',
            password='password',
            user='admin'
        ))

        with patch('ansible.module_utils.basic.AnsibleModule.fail_json', unsafe=True) as mo:
            AnsibleF5Client(
                argument_spec=self.spec.argument_spec,
                supports_check_mode=self.spec.supports_check_mode,
                f5_product_name=self.spec.f5_product_name,
                mutually_exclusive=self.spec.mutually_exclusive,
            )
            mo.assert_called_once()
