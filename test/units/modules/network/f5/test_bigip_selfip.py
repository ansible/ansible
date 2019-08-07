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
    from library.modules.bigip_selfip import ApiParameters
    from library.modules.bigip_selfip import ModuleParameters
    from library.modules.bigip_selfip import ModuleManager
    from library.modules.bigip_selfip import ArgumentSpec

    from library.module_utils.network.f5.common import F5ModuleError

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock
    from test.units.compat.mock import patch

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_selfip import ApiParameters
    from ansible.modules.network.f5.bigip_selfip import ModuleParameters
    from ansible.modules.network.f5.bigip_selfip import ModuleManager
    from ansible.modules.network.f5.bigip_selfip import ArgumentSpec

    from ansible.module_utils.network.f5.common import F5ModuleError

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
            address='10.10.10.10',
            allow_service=[
                'tcp:80',
                'udp:53',
                'gre'
            ],
            name='net1',
            netmask='255.255.255.0',
            partition='Common',
            route_domain='1',
            state='present',
            traffic_group='traffic-group-local-only',
            vlan='net1'
        )
        p = ModuleParameters(params=args)
        assert p.address == '10.10.10.10%1/24'
        assert p.allow_service == ['gre:0', 'tcp:80', 'udp:53']
        assert p.name == 'net1'
        assert p.netmask == 24
        assert p.route_domain == 1
        assert p.traffic_group == '/Common/traffic-group-local-only'
        assert p.vlan == '/Common/net1'

    def test_module_invalid_service(self):
        args = dict(
            allow_service=[
                'tcp:80',
                'udp:53',
                'grp'
            ]
        )
        p = ModuleParameters(params=args)
        with pytest.raises(F5ModuleError) as ex:
            assert p.allow_service == ['grp', 'tcp:80', 'udp:53']
        assert 'The provided protocol' in str(ex.value)

    def test_api_parameters(self):
        args = dict(
            address='10.10.10.10%1/24',
            allowService=[
                'tcp:80',
                'udp:53',
                'gre'
            ],
            name='net1',
            state='present',
            trafficGroup='/Common/traffic-group-local-only',
            vlan='net1'
        )
        p = ApiParameters(params=args)
        assert p.address == '10.10.10.10%1/24'
        assert p.allow_service == ['gre', 'tcp:80', 'udp:53']
        assert p.name == 'net1'
        assert p.netmask == 24
        assert p.traffic_group == '/Common/traffic-group-local-only'
        assert p.vlan == '/Common/net1'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_selfip(self, *args):
        set_module_args(dict(
            address='10.10.10.10',
            allow_service=[
                'tcp:80',
                'udp:53',
                'gre'
            ],
            name='net1',
            netmask='255.255.255.0',
            partition='Common',
            route_domain='1',
            state='present',
            traffic_group='traffic-group-local-only',
            vlan='net1',
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
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True

    def test_create_selfip_idempotent(self, *args):
        set_module_args(dict(
            address='10.10.10.10',
            allow_service=[
                'tcp:80',
                'udp:53',
                'gre'
            ],
            name='net1',
            netmask='255.255.255.0',
            partition='Common',
            route_domain='1',
            state='present',
            traffic_group='traffic-group-local-only',
            vlan='net1',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        current = ApiParameters(params=load_fixture('load_tm_net_self.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, True])
        mm.read_current_from_device = Mock(return_value=current)

        results = mm.exec_module()

        assert results['changed'] is False
