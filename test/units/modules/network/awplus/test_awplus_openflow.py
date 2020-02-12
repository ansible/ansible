from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_openflow
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusOpenFlowModule(TestAwplusModule):
    module = awplus_openflow

    def setUp(self):
        super(TestAwplusOpenFlowModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_openflow.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_openflow.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch(
            'ansible.modules.network.awplus.awplus_openflow.get_openflow_config')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestAwplusOpenFlowModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture(
            'awplus_openflow_config.cfg')
        self.load_config.return_value = None

        def load_from_file(*args, **kwargs):
            return load_fixture('awplus_openflow_config.cfg')

        self.run_commands.side_effect = load_from_file

    def test_awplus_openflow_add_existing_controller(self):
        set_module_args(dict(
            controllers=[dict(
                name='test_ssl1',
                protocol='ssl',
                address='192.56.8.3',
                ssl_port=8
            )],
            state="present"
        ))
        result = self.execute_module(failed=True, changed=False)
        self.assertEqual(
            'Controller already exists, please use a different address/ssl port', result['msg'])

    def test_awplus_openflow_add_new_controller(self):
        set_module_args(dict(
            controllers=[dict(
                protocol='tcp',
                address='184.5.3.2',
                ssl_port=10
            )]
        ))
        commands = ['openflow controller tcp 184.5.3.2 10']
        result = self.execute_module(changed=True)
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_remove_existing_controller(self):
        set_module_args(dict(
            controllers=[dict(
                name='test_ssl1',
                protocol='ssl',
                address='192.56.8.3',
                ssl_port=8
            )],
            state='absent'
        ))
        result = self.execute_module(changed=True)
        commands = ['no openflow controller test_ssl1']
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_remove_nonexisitng_controller(self):
        set_module_args(dict(
            controllers=[dict(
                name='oc2',
                protocol='ssl',
                address='192.56.8.3',
                ssl_port=8
            )],
            state='absent'
        ))
        self.execute_module(changed=False)

    def test_awplus_openflow_add_existing_port(self):
        set_module_args(dict(
            ports=[dict(
                name='port1.0.1',
                openflow=True
            )]
        ))
        self.execute_module(changed=False)

    def test_awplus_openflow_add_new_port(self):
        set_module_args(dict(
            ports=[dict(
                name='port1.0.2',
                openflow=True
            )]
        ))
        result = self.execute_module(changed=True)
        commands = ['interface port1.0.2', 'openflow']
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_edit_port(self):
        set_module_args(dict(
            ports=[dict(
                name='port1.0.1',
                openflow=False
            )]
        ))
        result = self.execute_module(changed=True)
        commands = ['interface port1.0.1', 'no openflow']
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_remove_existing_port(self):
        set_module_args(dict(
            ports=[dict(
                name='port1.0.1'
            )],
            state='absent'
        ))
        result = self.execute_module(changed=True)
        commands = ['interface port1.0.1', 'no openflow']
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_remove_nonexisting_port(self):
        set_module_args(dict(
            ports=[dict(
                name='port1.0.2'
            )],
            state='absent'
        ))
        self.execute_module(changed=False)

    def test_awplus_openflow_modify_native_vlan(self):
        set_module_args(dict(
            native_vlan=3
        ))
        commands = ['openflow native vlan 3']
        result = self.execute_module(changed=True)
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_default_native_vlan(self):
        set_module_args(dict(
            native_vlan=2,
            state='absent'
        ))
        commands = ['no openflow native vlan']
        result = self.execute_module(changed=True)
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_modify_fail_mode(self):
        set_module_args(dict(
            fail_mode='secure'
        ))
        commands = ['openflow failmode secure non-rule-expired']
        result = self.execute_module(changed=True)
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_default_fail_mode(self):
        set_module_args(dict(
            fail_mode='standalone',
            state='absent'
        ))
        commands = ['no openflow failmode']
        result = self.execute_module(changed=True)
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_remove_all_config(self):
        set_module_args(dict(
            state='absent'
        ))
        commands = ['no openflow controller test_ssl1',
                    'no openflow controller oc1',
                    'no openflow controller test_ssl',
                    'no openflow controller controller1',
                    'interface port1.0.1', 'no openflow',
                    'no openflow native vlan',
                    'no openflow failmode']
        result = self.execute_module(changed=True)
        self.assertEqual(commands, result['commands'])

    def test_awplus_openflow_invalid_port_name(self):
        set_module_args(dict(
            ports=[dict(
                name='vlan1',
                openflow=True
            )]
        ))
        result = self.execute_module(changed=False, failed=True)
        self.assertEqual('Invalid port name', result['msg'])
