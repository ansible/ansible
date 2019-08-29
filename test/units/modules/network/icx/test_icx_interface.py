# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from units.compat.mock import patch
from ansible.modules.network.icx import icx_interface
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXInterfaceModule(TestICXModule):

    module = icx_interface

    def setUp(self):
        super(TestICXInterfaceModule, self).setUp()
        self.mock_exec_command = patch('ansible.modules.network.icx.icx_interface.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_load_config = patch('ansible.modules.network.icx.icx_interface.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.icx.icx_interface.get_config')
        self.get_config = self.mock_get_config.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXInterfaceModule, self).tearDown()
        self.mock_exec_command.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_file(*args, **kwargs):
            module, commands, val = args
            for arg in args:
                if arg.params['check_running_config'] is True:
                    self.exec_command.return_value = (0, load_fixture('icx_interface_config.cfg').strip(), None)
                    return load_fixture('icx_interface_config.cfg').strip()
                else:
                    self.exec_command.return_value = 0, '', None
                    return ''

        self.get_config.side_effect = load_file
        self.load_config.return_value = None

    def test_icx_interface_set_config(self):
        power = dict(dict(enabled='True'))
        set_module_args(dict(name='ethernet 1/1/1', description='welcome port', speed='1000-full', power=power))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface ethernet 1/1/1',
                'speed-duplex 1000-full',
                'port-name welcome port',
                'inline power',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface ethernet 1/1/1',
                'speed-duplex 1000-full',
                'port-name welcome port',
                'inline power'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_interface_remove(self):
        set_module_args(dict(name='ethernet 1/1/1', state='absent'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['no interface ethernet 1/1/1'])
        else:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['no interface ethernet 1/1/1'])

    def test_icx_interface_disable(self):
        set_module_args(dict(name='ethernet 1/1/1', enabled=False))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['interface ethernet 1/1/1', 'disable'])
        else:
            result = self.execute_module(changed=True)
            self.assertEqual(result['commands'], ['interface ethernet 1/1/1', 'disable'])

    def test_icx_interface_set_power(self):
        power = dict(by_class='2')
        set_module_args(dict(name='ethernet 1/1/2', power=dict(power)))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface ethernet 1/1/2',
                'inline power power-by-class 2',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface ethernet 1/1/2',
                'inline power power-by-class 2'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_interface_aggregate(self):
        power = dict(dict(enabled='True'))
        aggregate = [
            dict(name='ethernet 1/1/9', description='welcome port9', speed='1000-full', power=power),
            dict(name='ethernet 1/1/10', description='welcome port10', speed='1000-full', power=power)
        ]
        set_module_args(dict(aggregate=aggregate))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface ethernet 1/1/9',
                'speed-duplex 1000-full',
                'port-name welcome port9',
                'inline power',
                'enable',
                'interface ethernet 1/1/10',
                'speed-duplex 1000-full',
                'port-name welcome port10',
                'inline power',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface ethernet 1/1/9',
                'speed-duplex 1000-full',
                'port-name welcome port9',
                'inline power',
                'enable',
                'interface ethernet 1/1/10',
                'speed-duplex 1000-full',
                'port-name welcome port10',
                'inline power',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_interface_lag_config(self):
        set_module_args(dict(name='lag 11', description='lag ports of id 11', speed='auto'))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface lag 11',
                'speed-duplex auto',
                'port-name lag ports of id 11',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface lag 11',
                'speed-duplex auto',
                'port-name lag ports of id 11'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_interface_loopback_config(self):
        set_module_args(dict(name='loopback 10', description='loopback ports', enabled=True))
        if not self.ENV_ICX_USE_DIFF:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface loopback 10',
                'port-name loopback ports',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)
        else:
            result = self.execute_module(changed=True)
            expected_commands = [
                'interface loopback 10',
                'port-name loopback ports',
                'enable'
            ]
            self.assertEqual(result['commands'], expected_commands)

    def test_icx_interface_state_up_cndt(self):
        set_module_args(dict(name='ethernet 1/1/1', state='up', tx_rate='ge(0)'))
        if not self.ENV_ICX_USE_DIFF:
            self.assertTrue(self.execute_module(failed=True))
        else:
            self.assertTrue(self.execute_module(failed=False))

    def test_icx_interface_lldp_neighbors_cndt(self):
        set_module_args(dict(name='ethernet 1/1/48', neighbors=[dict(port='GigabitEthernet1/1/48', host='ICX7150-48 Router')]))
        if not self.ENV_ICX_USE_DIFF:
            self.assertTrue(self.execute_module(changed=False, failed=True))
        else:
            self.assertTrue(self.execute_module(changed=False, failed=False))

    def test_icx_interface_disable_compare(self):
        set_module_args(dict(name='ethernet 1/1/1', enabled=True, check_running_config='True'))
        if self.get_running_config(compare=True):
            if not self.ENV_ICX_USE_DIFF:
                result = self.execute_module(changed=False)
                self.assertEqual(result['commands'], [])
            else:
                result = self.execute_module(changed=False)
                self.assertEqual(result['commands'], [])
