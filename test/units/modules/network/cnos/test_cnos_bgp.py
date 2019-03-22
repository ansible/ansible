from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_bgp
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosBgpModule(TestCnosModule):

    module = cnos_bgp

    def setUp(self):
        super(TestCnosBgpModule, self).setUp()

        self.mock_run_cnos_commands = patch('ansible.module_utils.network.cnos.cnos.run_cnos_commands')
        self.run_cnos_commands = self.mock_run_cnos_commands.start()

    def tearDown(self):
        super(TestCnosBgpModule, self).tearDown()
        self.mock_run_cnos_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.run_cnos_commands.return_value = [load_fixture('cnos_bgp_config.cfg')]

    def test_bgp_neighbor(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'neighbor', 'bgpArg2': '10.241.107.40',
                         'bgpArg3': '13', 'bgpArg4': 'address-family',
                         'bgpArg5': 'ipv4', 'bgpArg6': 'next-hop-self'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_bgp_dampening(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'address-family', 'bgpArg2': 'ipv4',
                         'bgpArg3': 'dampening', 'bgpArg4': '13',
                         'bgpArg5': '233', 'bgpArg6': '333',
                         'bgpArg7': '15', 'bgpArg8': '33'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_bgp_network(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'address-family', 'bgpArg2': 'ipv4',
                         'bgpArg3': 'network', 'bgpArg4': '1.2.3.4/5',
                         'bgpArg5': 'backdoor'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_bgp_clusterid(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'cluster-id', 'bgpArg2': '10.241.107.40'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_bgp_graceful_restart(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'graceful-restart', 'bgpArg2': '333'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_bgp_routerid(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'router-id', 'bgpArg2': '1.2.3.4'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)

    def test_cnos_bgp_vrf(self):
        set_module_args({'username': 'admin', 'password': 'pass',
                         'host': '10.241.107.39', 'deviceType': 'g8272_cnos',
                         'outputfile': self.test_log, 'asNum': '33',
                         'bgpArg1': 'vrf'})
        result = self.execute_module(changed=True)
        expected_result = 'BGP configurations accomplished'
        self.assertEqual(result['msg'], expected_result)
