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
    from library.modules.bigip_snat_translation import ApiParameters
    from library.modules.bigip_snat_translation import ModuleParameters
    from library.modules.bigip_snat_translation import ModuleManager
    from library.modules.bigip_snat_translation import ArgumentSpec

    # In Ansible 2.8, Ansible changed import paths.
    from test.units.compat import unittest
    from test.units.compat.mock import Mock

    from test.units.modules.utils import set_module_args
except ImportError:
    from ansible.modules.network.f5.bigip_snat_translation import ApiParameters
    from ansible.modules.network.f5.bigip_snat_translation import ModuleParameters
    from ansible.modules.network.f5.bigip_snat_translation import ModuleManager
    from ansible.modules.network.f5.bigip_snat_translation import ArgumentSpec

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
            name='my-snat-translation',
            address='1.1.1.1',
            arp='yes',
            connection_limit=300,
            description='None',
            ip_idle_timeout='50',
            partition='Common',
            state='present',
            traffic_group='test',
            tcp_idle_timeout='20',
            udp_idle_timeout='100',
        )

        p = ModuleParameters(params=args)
        assert p.name == 'my-snat-translation'
        assert p.address == '1.1.1.1'
        assert p.arp == 'enabled'
        assert p.connection_limit == 300
        assert p.description == 'None'
        assert p.ip_idle_timeout == '50'
        assert p.partition == 'Common'
        assert p.state == 'present'
        assert p.traffic_group == '/Common/test'
        assert p.tcp_idle_timeout == '20'
        assert p.udp_idle_timeout == '100'

    def test_api_parameters(self):
        args = load_fixture('load_ltm_snat_translation_default.json')
        p = ApiParameters(params=args)
        assert p.address == '1.1.1.1'
        assert p.arp == 'no'
        assert p.connection_limit == 0
        assert p.description == 'My description'
        assert p.ip_idle_timeout == '50'
        assert p.partition == 'Common'
        assert p.traffic_group == '/Common/test'
        assert p.tcp_idle_timeout == '20'
        assert p.udp_idle_timeout == '100'

    def test_module_parameters_arp_yes(self):
        args = dict(
            arp='yes'
        )
        p = ModuleParameters(params=args)
        assert p.arp == 'enabled'

    def test_module_parameters_arp_no(self):
        args = dict(
            arp='no'
        )
        p = ModuleParameters(params=args)
        assert p.arp == 'disabled'

    def test_module_parameters_connection_limit_none(self):
        args = dict(
            connection_limit=0
        )
        p = ModuleParameters(params=args)
        assert p.connection_limit == 0

    def test_module_parameters_connection_limit_int(self):
        args = dict(
            connection_limit=500
        )
        p = ModuleParameters(params=args)
        assert p.connection_limit == 500

    def test_module_parameters_description_none(self):
        args = dict(
            description='none'
        )
        p = ModuleParameters(params=args)
        assert p.description == ''

    def test_module_parameters_description_empty(self):
        args = dict(
            description=''
        )
        p = ModuleParameters(params=args)
        assert p.description == ''

    def test_module_parameters_description_string_value(self):
        args = dict(
            description='My Snat Translation'
        )
        p = ModuleParameters(params=args)
        assert p.description == 'My Snat Translation'

    def test_module_parameters_ip_idle_timeout_indefinite(self):
        args = dict(
            ip_idle_timeout='indefinite'
        )
        p = ModuleParameters(params=args)
        assert p.ip_idle_timeout == 'indefinite'

    def test_module_parameters_ip_idle_timeout_string_value(self):
        args = dict(
            ip_idle_timeout='65000'
        )
        p = ModuleParameters(params=args)
        assert p.ip_idle_timeout == '65000'

    def test_module_no_partition_prefix_parameters(self):
        args = dict(
            partition='Common',
            address='10.10.10.10',
            traffic_group='traffic-group-1'
        )
        p = ModuleParameters(params=args)
        assert p.partition == 'Common'
        assert p.address == '10.10.10.10'
        assert p.traffic_group == '/Common/traffic-group-1'

    def test_module_partition_prefix_parameters(self):
        args = dict(
            partition='Common',
            address='10.10.10.10',
            traffic_group='/Common/traffic-group-1'
        )
        p = ModuleParameters(params=args)
        assert p.partition == 'Common'
        assert p.address == '10.10.10.10'
        assert p.traffic_group == '/Common/traffic-group-1'

    def test_module_parameters_state_present(self):
        args = dict(
            state='present'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'present'
        assert p.enabled is True

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
        assert p.enabled is True

    def test_module_parameters_state_disabled(self):
        args = dict(
            state='disabled'
        )
        p = ModuleParameters(params=args)
        assert p.state == 'disabled'
        assert p.disabled is True

    def test_module_parameters_tcp_idle_timeout_indefinite(self):
        args = dict(
            tcp_idle_timeout='indefinite'
        )
        p = ModuleParameters(params=args)
        assert p.tcp_idle_timeout == 'indefinite'

    def test_module_parameters_tcp_idle_timeout_string_value(self):
        args = dict(
            tcp_idle_timeout='65000'
        )
        p = ModuleParameters(params=args)
        assert p.tcp_idle_timeout == '65000'

    def test_module_parameters_udp_idle_timeout_indefinite(self):
        args = dict(
            udp_idle_timeout='indefinite'
        )
        p = ModuleParameters(params=args)
        assert p.udp_idle_timeout == 'indefinite'

    def test_module_parameters_udp_idle_timeout_string_value(self):
        args = dict(
            udp_idle_timeout='65000'
        )
        p = ModuleParameters(params=args)
        assert p.udp_idle_timeout == '65000'


class TestManager(unittest.TestCase):
    def setUp(self):
        self.spec = ArgumentSpec()

    def test_create_snat_translation(self, *args):
        set_module_args(dict(
            name='my-snat-translation',
            address='1.1.1.1',
            arp='yes',
            connection_limit=300,
            description='My description',
            ip_idle_timeout='50',
            state='present',
            tcp_idle_timeout='20',
            udp_idle_timeout='100',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.exists = Mock(side_effect=[False, True])
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['address'] == '1.1.1.1'
        assert results['arp'] == 'yes'
        assert results['connection_limit'] == 300
        assert results['description'] == 'My description'
        assert results['ip_idle_timeout'] == '50'
        assert results['tcp_idle_timeout'] == '20'
        assert results['udp_idle_timeout'] == '100'

    def test_update_snat_translation(self, *args):
        set_module_args(dict(
            name='my-snat-translation',
            address='1.1.1.1',
            arp='yes',
            connection_limit=300,
            description='',
            ip_idle_timeout='500',
            state='disabled',
            tcp_idle_timeout='indefinite',
            traffic_group='traffic-group-1',
            udp_idle_timeout='indefinite',
            provider=dict(
                server='localhost',
                password='password',
                user='admin'
            )
        ))
        current = ApiParameters(params=load_fixture('load_ltm_snat_translation_default.json'))

        module = AnsibleModule(
            argument_spec=self.spec.argument_spec,
            supports_check_mode=self.spec.supports_check_mode,
            required_if=self.spec.required_if
        )
        mm = ModuleManager(module=module)

        # Override methods to force specific logic in the module to happen
        mm.read_current_from_device = Mock(return_value=current)
        mm.update_on_device = Mock(return_value=True)
        mm.exists = Mock(return_value=True)
        mm.create_on_device = Mock(return_value=True)

        results = mm.exec_module()

        assert results['changed'] is True
        assert results['arp'] == 'yes'
        assert results['connection_limit'] == 300
        assert results['description'] == ''
        assert results['ip_idle_timeout'] == '500'
        assert results['tcp_idle_timeout'] == 'indefinite'
        assert results['udp_idle_timeout'] == 'indefinite'
