# -*- coding: utf-8 -*-
#
# Copyright: (c) 2019, F5 Networks Inc.
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
    from library.modules.bigip_message_routing_protocol import ApiParameters
    from library.modules.bigip_message_routing_protocol import ModuleParameters
    from library.modules.bigip_message_routing_protocol import ModuleManager
    from library.modules.bigip_message_routing_protocol import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_message_routing_protocol import ApiParameters
    from ansible.modules.network.f5.bigip_message_routing_protocol import ModuleParameters
    from ansible.modules.network.f5.bigip_message_routing_protocol import ModuleManager
    from ansible.modules.network.f5.bigip_message_routing_protocol import ArgumentSpec

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
            name='foo',
            partition='foobar',
            description='my description',
            parent='barfoo',
            disable_parser=True,
            max_egress_buffer=10000,
            max_msg_size=2000,
            msg_terminator='%%%%',
            no_response=False,
        )

        p = ModuleParameters(params=args)
        assert p.name == 'foo'
        assert p.partition == 'foobar'
        assert p.description == 'my description'
        assert p.parent == '/foobar/barfoo'
        assert p.disable_parser == 'yes'
        assert p.max_egress_buffer == 10000
        assert p.max_msg_size == 2000
        assert p.msg_terminator == '%%%%'
        assert p.no_response == 'no'

    def test_api_parameters(self):
        args = load_fixture('load_generic_parser.json')

        p = ApiParameters(params=args)
        assert p.name == 'foobar'
        assert p.partition == 'Common'
        assert p.parent == '/Common/genericmsg'
        assert p.disable_parser == 'no'
        assert p.max_egress_buffer == 32768
        assert p.max_msg_size == 32768
        assert p.no_response == 'no'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_generic_protocol(self, *args):
        set_module_args(dict(
            name='foo',
            partition='foobar',
            description='my description',
            parent='barfoo',
            disable_parser=True,
            max_egress_buffer=10000,
            max_msg_size=2000,
            msg_terminator='%%%%',
            no_response=False,
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
        mm.exists = Mock(return_value=False)
        mm.create_on_device = Mock(return_value=True)
        mm.version_less_than_14 = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['description'] == 'my description'
        assert results['parent'] == '/foobar/barfoo'
        assert results['disable_parser'] == 'yes'
        assert results['max_egress_buffer'] == 10000
        assert results['max_msg_size'] == 2000
        assert results['msg_terminator'] == '%%%%'
        assert results['no_response'] == 'no'

    def test_update_generic_protocol(self, *args):
        set_module_args(dict(
            name='foobar',
            disable_parser=True,
            max_egress_buffer=10000,
            max_msg_size=2000,
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_generic_parser.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )

        # Override methods in the specific type of manager
        mm = ModuleManager(module=module)
        mm.exists = Mock(return_value=True)
        mm.update_on_device = Mock(return_value=True)
        mm.read_current_from_device = Mock(return_value=current)
        mm.version_less_than_14 = Mock(return_value=False)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['disable_parser'] == 'yes'
        assert results['max_egress_buffer'] == 10000
        assert results['max_msg_size'] == 2000
