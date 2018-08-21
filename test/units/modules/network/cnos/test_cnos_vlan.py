from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from ansible.compat.tests.mock import patch
from ansible.modules.network.cnos import cnos_vlan
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosVlanModule(TestCnosModule):

    module = cnos_vlan

    def setUp(self):
        super(TestCnosVlanModule, self).setUp()

        self.mock_run_cnos_commands = patch('ansible.module_utils.network.cnos.cnos.run_cnos_commands')
        self.run_cnos_commands = self.mock_run_cnos_commands.start()

    def tearDown(self):
        super(TestCnosVlanModule, self).tearDown()
        self.mock_run_cnos_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.run_cnos_commands.return_value = [load_fixture('cnos_vlan_config.cfg')]

    def test_cnos_vlan_create(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'vlanArg1': '13',
                         'vlanArg2': 'name', 'vlanArg3': 'anil'})
        result = self.execute_module(changed=True)
        file = open('Anil.txt', "a")
        file.write(str(result))
        file.close()
        expected_result = 'VLAN configuration is accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_vlan_state(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'vlanArg1': '13',
                         'vlanArg2': 'state', 'vlanArg3': 'active'})
        result = self.execute_module(changed=True)
        expected_result = 'VLAN configuration is accomplished'
        self.assertEqual(result['msg'], expected_result)
