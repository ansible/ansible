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
from ansible.compat.tests.mock import patch, DEFAULT, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_snmp_trap import NetworkedParameters
    from library.bigip_snmp_trap import NonNetworkedParameters
    from library.bigip_snmp_trap import ModuleManager
    from library.bigip_snmp_trap import NetworkedManager
    from library.bigip_snmp_trap import NonNetworkedManager
    from library.bigip_snmp_trap import ArgumentSpec
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_snmp_trap import NetworkedParameters
        from ansible.modules.network.f5.bigip_snmp_trap import NonNetworkedParameters
        from ansible.modules.network.f5.bigip_snmp_trap import ModuleManager
        from ansible.modules.network.f5.bigip_snmp_trap import NetworkedManager
        from ansible.modules.network.f5.bigip_snmp_trap import NonNetworkedManager
        from ansible.modules.network.f5.bigip_snmp_trap import ArgumentSpec
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
    def test_module_networked_parameters(self):
        args = dict(
            name='foo',
            snmp_version='1',
            community='public',
            destination='10.10.10.10',
            port=1000,
            network='other',
            password='password',
            server='localhost',
            user='admin'
        )
        p = NetworkedParameters(args)
        assert p.name == 'foo'
        assert p.snmp_version == '1'
        assert p.community == 'public'
        assert p.destination == '10.10.10.10'
        assert p.port == 1000
        assert p.network == 'other'

    def test_module_non_networked_parameters(self):
        args = dict(
            name='foo',
            snmp_version='1',
            community='public',
            destination='10.10.10.10',
            port=1000,
            network='other',
            password='password',
            server='localhost',
            user='admin'
        )
        p = NonNetworkedParameters(args)
        assert p.name == 'foo'
        assert p.snmp_version == '1'
        assert p.community == 'public'
        assert p.destination == '10.10.10.10'
        assert p.port == 1000
        assert p.network is None

    def test_api_parameters(self):
        args = dict(
            name='foo',
            community='public',
            host='10.10.10.10',
            network='other',
            version=1,
            port=1000
        )
        p = NetworkedParameters(args)
        assert p.name == 'foo'
        assert p.snmp_version == '1'
        assert p.community == 'public'
        assert p.destination == '10.10.10.10'
        assert p.port == 1000
        assert p.network == 'other'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_trap(self, *args):
        set_module_args(dict(
            name='foo',
            snmp_version='1',
            community='public',
            destination='10.10.10.10',
            port=1000,
            network='other',
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_non_networked = Mock(return_value=False)

        patches = dict(
            create_on_device=DEFAULT,
            exists=DEFAULT
        )
        with patch.multiple(NetworkedManager, **patches) as mo:
            mo['create_on_device'].side_effect = Mock(return_value=True)
            mo['exists'].side_effect = Mock(return_value=False)
            results = mm.exec_module()

        assert results['changed'] is True
        assert results['port'] == 1000
        assert results['snmp_version'] == '1'

    def test_create_trap_non_network(self, *args):
        set_module_args(dict(
            name='foo',
            snmp_version='1',
            community='public',
            destination='10.10.10.10',
            port=1000,
            password='password',
            server='localhost',
            user='admin'
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )

        # Override methods to force specific logic in the module to happen
        mm = ModuleManager(client)
        mm.is_version_non_networked = Mock(return_value=True)

        patches = dict(
            create_on_device=DEFAULT,
            exists=DEFAULT
        )
        with patch.multiple(NonNetworkedManager, **patches) as mo:
            mo['create_on_device'].side_effect = Mock(return_value=True)
            mo['exists'].side_effect = Mock(return_value=False)
            results = mm.exec_module()

        assert results['changed'] is True
        assert results['port'] == 1000
        assert results['snmp_version'] == '1'
