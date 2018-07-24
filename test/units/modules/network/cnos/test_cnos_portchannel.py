from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
from ansible.compat.tests.mock import patch
from ansible.modules.network.cnos import cnos_portchannel
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosPortchannelModule(TestCnosModule):

    module = cnos_portchannel

    def setUp(self):
        super(TestCnosPortchannelModule, self).setUp()

        self.mock_run_cnos_commands = patch('ansible.module_utils.network.cnos.cnos.run_cnos_commands')
        self.run_cnos_commands = self.mock_run_cnos_commands.start()

    def tearDown(self):
        super(TestCnosPortchannelModule, self).tearDown()
        self.mock_run_cnos_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.run_cnos_commands.return_value = [load_fixture('cnos_portchannel_config.cfg')]

    def test_portchannel_channelgroup(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'interfaceRange': '33',
                         'interfaceArg1': 'channel-group', 'interfaceArg2': '33', 'interfaceArg3': 'on'})
        result = self.execute_module(changed=True)
        file = open('Anil.txt', "a")
        file.write(str(result))
        file.close()
        expected_result = 'Port Channel Configuration is done'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_portchannel_lacp(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'interfaceRange': '33',
                         'interfaceArg1': 'lacp', 'interfaceArg2': 'port-priority', 'interfaceArg3': '33'})
        result = self.execute_module(changed=True)
        expected_result = 'Port Channel Configuration is done'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_portchannel_duplex(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'interfaceRange': '2',
                         'interfaceArg1': 'duplex', 'interfaceArg2': 'auto'})
        result = self.execute_module(changed=True)
        expected_result = 'Port Channel Configuration is done'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_portchannel_mtu(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'interfaceRange': '33',
                         'interfaceArg1': 'mtu', 'interfaceArg2': '1300'})
        result = self.execute_module(changed=True)
        expected_result = 'Port Channel Configuration is done'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_portchannel_spanningtree(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'interfaceRange': '33',
                         'interfaceArg1': 'spanning-tree', 'interfaceArg2': 'mst',
                         'interfaceArg3': '33-35', 'interfaceArg4': 'cost',
                         'interfaceArg5': '33'})
        result = self.execute_module(changed=True)
        expected_result = 'Port Channel Configuration is done'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_portchannel_ip(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': 'test.log', 'interfaceRange': '33',
                         'interfaceArg1': 'ip', 'interfaceArg2': 'port',
                         'interfaceArg3': 'anil'})
        result = self.execute_module(changed=True)
        expected_result = 'Port Channel Configuration is done'
        self.assertEqual(result['msg'], expected_result)
