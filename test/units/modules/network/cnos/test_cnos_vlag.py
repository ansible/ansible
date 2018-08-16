from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from ansible.compat.tests.mock import patch
from ansible.modules.network.cnos import cnos_vlag
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosVlagModule(TestCnosModule):

    module = cnos_vlag

    def setUp(self):
        super(TestCnosVlagModule, self).setUp()

        self.mock_run_cnos_commands = patch('ansible.module_utils.network.cnos.cnos.run_cnos_commands')
        self.run_cnos_commands = self.mock_run_cnos_commands.start()

    def tearDown(self):
        super(TestCnosVlagModule, self).tearDown()
        self.mock_run_cnos_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.run_cnos_commands.return_value = [load_fixture('cnos_vlag_config.cfg')]

    def test_cnos_vlag_enable(self):
        set_module_args({'username': 'admin', 'password': 'admin',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'vlagArg1': 'enable'})
        result = self.execute_module(changed=True)
        file = open('Anil.txt', "a")
        file.write(str(result))
        file.close()
        expected_result = 'VLAG configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_vlag_instance(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'vlagArg1': 'instance',
                         'vlagArg2': '33', 'vlagArg3': '333'})
        result = self.execute_module(changed=True)
        expected_result = 'VLAG configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_vlag_hlthchk(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'vlagArg1': 'hlthchk',
                         'vlagArg2': 'keepalive-interval', 'vlagArg3': '131'})
        result = self.execute_module(changed=True)
        expected_result = 'VLAG configurations accomplished'
        self.assertEqual(result['msg'], expected_result)
