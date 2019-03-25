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
    from library.modules.bigip_snmp_trap import V2Parameters
    from library.modules.bigip_snmp_trap import V1Parameters
    from library.modules.bigip_snmp_trap import ModuleManager
    from library.modules.bigip_snmp_trap import V2Manager
    from library.modules.bigip_snmp_trap import V1Manager
    from library.modules.bigip_snmp_trap import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch
    from test.units.compat.mock import DEFAULT

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_snmp_trap import V2Parameters
    from ansible.modules.network.f5.bigip_snmp_trap import V1Parameters
    from ansible.modules.network.f5.bigip_snmp_trap import ModuleManager
    from ansible.modules.network.f5.bigip_snmp_trap import V2Manager
    from ansible.modules.network.f5.bigip_snmp_trap import V1Manager
    from ansible.modules.network.f5.bigip_snmp_trap import ArgumentSpec

    # Ansible 2.8 imports
    from units.compat import unittest
    from units.compat.mock import Mock
    from units.compat.mock import patch
    from units.compat.mock import DEFAULT

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
    def test_module_networked_parameters(self):
        args = dict(
            name='foo',
            snmp_version='1',
            community='public',
            destination='10.10.10.10',
            port=1000,
            network='other',
        )
        p = V2Parameters(params=args)
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
        )
        p = V1Parameters(params=args)
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
        p = V2Parameters(params=args)
        assert p.name == 'foo'
        assert p.snmp_version == '1'
        assert p.community == 'public'
        assert p.destination == '10.10.10.10'
        assert p.port == 1000
        assert p.network == 'other'


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

        # Override methods to force specific logic in the module to happen
        m0 = ModuleManager(module=module)
        m0.is_version_without_network = Mock(return_value=False)
        m0.is_version_with_default_network = Mock(return_value=True)

        patches = dict(
            create_on_device=DEFAULT,
            exists=DEFAULT
        )
        with patch.multiple(V2Manager, **patches) as mo:
            mo['create_on_device'].side_effect = Mock(return_value=True)
            mo['exists'].side_effect = Mock(return_value=False)
            results = m0.exec_module()

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

        # Override methods to force specific logic in the module to happen
        m0 = ModuleManager(module=module)
        m0.is_version_without_network = Mock(return_value=True)

        patches = dict(
            create_on_device=DEFAULT,
            exists=DEFAULT
        )
        with patch.multiple(V1Manager, **patches) as mo:
            mo['create_on_device'].side_effect = Mock(return_value=True)
            mo['exists'].side_effect = Mock(return_value=False)
            results = m0.exec_module()

        assert results['changed'] is True
        assert results['port'] == 1000
        assert results['snmp_version'] == '1'
