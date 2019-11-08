# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from units.compat.mock import patch
from ansible.modules.network.icx import icx_static_route
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXStaticRouteModule(TestICXModule):

    module = icx_static_route

    def setUp(self):
        super(TestICXStaticRouteModule, self).setUp()
        self.mock_get_config = patch('ansible.modules.network.icx.icx_static_route.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.icx.icx_static_route.load_config')
        self.load_config = self.mock_load_config.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXStaticRouteModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg.params['check_running_config'] is True:
                    return load_fixture('icx_static_route_config.txt').strip()
                else:
                    return ''

        self.get_config.side_effect = load_file
        self.load_config.return_value = None

    def test_icx_static_route_config(self):
        set_module_args(dict(prefix='192.126.23.0/24', next_hop='10.10.14.3'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'ip route 192.126.23.0 255.255.255.0 10.10.14.3'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'ip route 192.126.23.0 255.255.255.0 10.10.14.3'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_static_route_config_compare(self):
        set_module_args(dict(prefix='172.16.10.0/24', next_hop='10.0.0.8', check_running_config=True))
        if self.get_running_config(compare=True):
            if not self.ENV_ICX_USE_DIFF:
                result = self.execute_module(changed=False)
                expected_commands = [
                ]
                self.assertEqual(result['commands'], expected_commands)
            else:
                result = self.execute_module(changed=False)
                expected_commands = [
                ]
                self.assertEqual(result['commands'], expected_commands)

    def test_icx_static_route_distance_config(self):
        set_module_args(dict(prefix='192.126.0.0', mask='255.255.0.0', next_hop='10.10.14.3', admin_distance='40'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'ip route 192.126.0.0 255.255.0.0 10.10.14.3 distance 40'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'ip route 192.126.0.0 255.255.0.0 10.10.14.3 distance 40'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_static_route_aggregate(self):
        aggregate = [
            dict(prefix='192.126.23.0/24', next_hop='10.10.14.3'),
            dict(prefix='192.126.0.0', mask='255.255.0.0', next_hop='10.10.14.3', admin_distance='40')
        ]
        set_module_args(dict(aggregate=aggregate))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'ip route 192.126.23.0 255.255.255.0 10.10.14.3',
                'ip route 192.126.0.0 255.255.0.0 10.10.14.3 distance 40'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'ip route 192.126.23.0 255.255.255.0 10.10.14.3',
                'ip route 192.126.0.0 255.255.0.0 10.10.14.3 distance 40'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_static_route_remove(self):
        set_module_args(dict(prefix='172.16.10.0/24', next_hop='10.0.0.8', state='absent'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'no ip route 172.16.10.0 255.255.255.0 10.0.0.8',
            ]
            self.assertEqual(result['commands'], expected_commands)

        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'no ip route 172.16.10.0 255.255.255.0 10.0.0.8',
            ]
            self.assertEqual(result['commands'], expected_commands)
