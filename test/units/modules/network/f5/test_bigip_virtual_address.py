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
from ansible.compat.tests.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible.module_utils.f5_utils import AnsibleF5Client

try:
    from library.bigip_virtual_address import Parameters
    from library.bigip_virtual_address import ModuleManager
    from library.bigip_virtual_address import ArgumentSpec
except ImportError:
    try:
        from ansible.modules.network.f5.bigip_virtual_address import Parameters
        from ansible.modules.network.f5.bigip_virtual_address import ModuleManager
        from ansible.modules.network.f5.bigip_virtual_address import ArgumentSpec
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
    def test_module_parameters(self):
        args = dict(
            state='present',
            address='1.1.1.1',
            netmask='2.2.2.2',
            connection_limit='10',
            arp_state='enabled',
            auto_delete='enabled',
            icmp_echo='enabled',
            advertise_route='always',
            use_route_advertisement='yes'
        )
        p = Parameters(args)
        assert p.state == 'present'
        assert p.address == '1.1.1.1'
        assert p.netmask == '2.2.2.2'
        assert p.connection_limit == 10
        assert p.arp_state == 'enabled'
        assert p.auto_delete is True
        assert p.icmp_echo == 'enabled'
        assert p.advertise_route == 'none'
        assert p.use_route_advertisement == 'enabled'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_virtual_address_default.json')
        p = Parameters(args)
        assert p.name == '1.1.1.1'
        assert p.address == '1.1.1.1'
        assert p.arp_state == 'enabled'
        assert p.auto_delete is True
        assert p.connection_limit == 0
        assert p.state == 'enabled'
        assert p.icmp_echo == 'enabled'
        assert p.netmask == '255.255.255.255'
        assert p.use_route_advertisement == 'disabled'
        assert p.advertise_route == 'any'

    def test_module_parameters_advertise_route_all(self):
        args = dict(
            advertise_route='when_all_available'
        )
        p = Parameters(args)
        assert p.advertise_route == 'all'

    def test_module_parameters_advertise_route_any(self):
        args = dict(
            advertise_route='when_any_available'
        )
        p = Parameters(args)
        assert p.advertise_route == 'any'

    def test_module_parameters_icmp_echo_disabled(self):
        args = dict(
            icmp_echo='disabled'
        )
        p = Parameters(args)
        assert p.icmp_echo == 'disabled'

    def test_module_parameters_icmp_echo_selective(self):
        args = dict(
            icmp_echo='selective'
        )
        p = Parameters(args)
        assert p.icmp_echo == 'selective'

    def test_module_parameters_auto_delete_disabled(self):
        args = dict(
            auto_delete='disabled'
        )
        p = Parameters(args)
        assert p.auto_delete is False

    def test_module_parameters_arp_state_disabled(self):
        args = dict(
            arp_state='disabled'
        )
        p = Parameters(args)
        assert p.arp_state == 'disabled'

    def test_module_parameters_use_route_advert_disabled(self):
        args = dict(
            use_route_advertisement='no'
        )
        p = Parameters(args)
        assert p.use_route_advertisement == 'disabled'

    def test_module_parameters_state_present(self):
        args = dict(
            state='present'
        )
        p = Parameters(args)
        assert p.state == 'present'
        assert p.enabled == 'yes'

    def test_module_parameters_state_absent(self):
        args = dict(
            state='absent'
        )
        p = Parameters(args)
        assert p.state == 'absent'

    def test_module_parameters_state_enabled(self):
        args = dict(
            state='enabled'
        )
        p = Parameters(args)
        assert p.state == 'enabled'
        assert p.enabled == 'yes'

    def test_module_parameters_state_disabled(self):
        args = dict(
            state='disabled'
        )
        p = Parameters(args)
        assert p.state == 'disabled'
        assert p.enabled == 'no'


@patch('ansible.module_utils.f5_utils.AnsibleF5Client._get_mgmt_root',
       return_value=True)
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
            use_route_advertisement='yes',
            password='admin',
            server='localhost',
            user='admin',
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True

    def test_delete_virtual_address(self, *args):
        set_module_args(dict(
            state='absent',
            address='1.1.1.1',
            password='admin',
            server='localhost',
            user='admin',
        ))

        client = AnsibleF5Client(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            f5_product_name=self.spec.f5_product_name
        )
        mm = ModuleManager(client)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[True, False])
        mm.remove_from_device = Mock(return_value=True)

        results = mm.exec_module()
        assert results['changed'] is True
