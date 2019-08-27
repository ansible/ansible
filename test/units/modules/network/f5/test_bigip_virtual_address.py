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
    from library.modules.bigip_virtual_address import ApiParameters
    from library.modules.bigip_virtual_address import ModuleParameters
    from library.modules.bigip_virtual_address import ModuleManager
    from library.modules.bigip_virtual_address import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_virtual_address import ApiParameters
    from ansible.modules.network.f5.bigip_virtual_address import ModuleParameters
    from ansible.modules.network.f5.bigip_virtual_address import ModuleManager
    from ansible.modules.network.f5.bigip_virtual_address import ArgumentSpec

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
            state='present',
            address='1.1.1.1',
            netmask='2.2.2.2',
            connection_limit='10',
            arp_state='enabled',
            auto_delete='enabled',
            icmp_echo='enabled',
            availability_calculation='always',
        )
        p = ModuleParameters(params=args)
        assert p.state == 'present'
        assert p.address == '1.1.1.1'
        assert p.netmask == '2.2.2.2'
        assert p.connection_limit == 10
        assert p.arp is True
        assert p.auto_delete is True
        assert p.icmp_echo == 'enabled'
        assert p.availability_calculation == 'none'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_virtual_address_default.json')
        p = ApiParameters(params=args)
        assert p.name == '1.1.1.1'
        assert p.address == '1.1.1.1'
        assert p.arp is True
        assert p.auto_delete is True
        assert p.connection_limit == 0
        assert p.state == 'enabled'
        assert p.icmp_echo == 'enabled'
        assert p.netmask == '255.255.255.255'
        assert p.route_advertisement_type == 'disabled'
        assert p.availability_calculation == 'any'

    def test_module_parameters_advertise_route_all(self):
        args = dict(
            availability_calculation='when_all_available'
        )
        p = ModuleParameters(params=args)
        assert p.availability_calculation == 'all'

    def test_module_parameters_advertise_route_any(self):
        args = dict(
            availability_calculation='when_any_available'
        )
        p = ModuleParameters(params=args)
        assert p.availability_calculation == 'any'

    def test_module_parameters_icmp_echo_disabled(self):
        args = dict(
            icmp_echo='disabled'
        )
        p = ModuleParameters(params=args)
        assert p.icmp_echo == 'disabled'

    def test_module_parameters_icmp_echo_selective(self):
        args = dict(
            icmp_echo='selective'
        )
        p = ModuleParameters(params=args)
        assert p.icmp_echo == 'selective'

    def test_module_parameters_auto_delete_disabled(self):
        args = dict(
            auto_delete='disabled'
        )
        p = ModuleParameters(params=args)
        assert p.auto_delete is False

    def test_module_parameters_arp_state_disabled(self):
        args = dict(
            arp_state='disabled'
        )
        p = ModuleParameters(params=args)
        assert p.arp_state == 'disabled'

    def test_module_parameters_state_present(self):
        args = dict(
            state='present'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'present'
        assert p.enabled == 'yes'

    def test_module_parameters_state_absent(self):
        args = dict(
            state='absent'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'absent'

    def test_module_parameters_state_enabled(self):
        args = dict(
            state='enabled'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'enabled'
        assert p.enabled == 'yes'

    def test_module_parameters_state_disabled(self):
        args = dict(
            state='disabled'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'disabled'
        assert p.enabled == 'no'


class TestManager(unittest.TestCase):

    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_virtual_address(self, *args):
        set_module_args(dict(
            state='present',
            address='1.1.1.1',
            netmask='2.2.2.2',
            connection_limit='10',
            arp_state='enabled',
            auto_delete='enabled',
            icmp_echo='enabled',
            advertise_route='always',
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
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True

    def test_delete_virtual_address(self, *args):
        set_module_args(dict(
            state='absent',
            address='1.1.1.1',
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
            required_one_of=self.spec.required_one_of
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, False])
        mm.remove_from_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
