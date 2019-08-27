# (c) 2016 Red Hat Inc.
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch, MagicMock
from ansible.modules.network.junos import junos_ping
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule, load_fixture


class TestJunosPingModule(TestJunosModule):
    module = junos_ping

    def setUp(self):
        super(TestJunosPingModule, self).setUp()

        self.mock_get_connection = patch('ansible.modules.network.junos.junos_ping.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.conn = self.get_connection()
        self.conn.get = MagicMock()

    def tearDown(self):
        super(TestJunosPingModule, self).tearDown()
        self.mock_get_connection.stop()

    def test_junos_ping_expected_success(self):
        set_module_args(dict(count=2, dest="10.10.10.10"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.10_count_2', content='str'))
        result = self.execute_module()
        self.assertEqual(result['commands'], 'ping 10.10.10.10 count 2')

    def test_junos_ping_expected_failure(self):
        set_module_args(dict(count=4, dest="10.10.10.20", state="absent"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.20_count_4', content='str'))
        result = self.execute_module()
        self.assertEqual(result['commands'], 'ping 10.10.10.20 count 4')

    def test_junos_ping_unexpected_success(self):
        ''' Test for successful pings when destination should not be reachable - FAIL. '''
        set_module_args(dict(count=2, dest="10.10.10.10", state="absent"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.10_count_2', content='str'))
        self.execute_module(failed=True)

    def test_junos_ping_unexpected_failure(self):
        ''' Test for unsuccessful pings when destination should be reachable - FAIL. '''
        set_module_args(dict(count=4, dest="10.10.10.20"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.20_count_4', content='str'))
        self.execute_module(failed=True)

    def test_junos_ping_failure_stats(self):
        '''Test for asserting stats when ping fails'''
        set_module_args(dict(count=4, dest="10.10.10.20"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.20_count_4', content='str'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['packet_loss'], '100%')
        self.assertEqual(result['packets_rx'], 0)
        self.assertEqual(result['packets_tx'], 4)

    def test_junos_ping_success_stats(self):
        set_module_args(dict(count=2, dest="10.10.10.10"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.10_count_2', content='str'))
        result = self.execute_module()
        self.assertEqual(result['commands'], 'ping 10.10.10.10 count 2')
        self.assertEqual(result['packet_loss'], '0%')
        self.assertEqual(result['packets_rx'], 2)
        self.assertEqual(result['packets_tx'], 2)
        self.assertEqual(result['rtt']['min'], 15.71)
        self.assertEqual(result['rtt']['avg'], 16.87)
        self.assertEqual(result['rtt']['max'], 18.04)
        self.assertEqual(result['rtt']['stddev'], 1.165)

    def test_junos_ping_success_stats_with_options(self):
        set_module_args(dict(count=5, size=512, interval=2, dest="10.10.10.11"))
        self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.10.10.11_count_5_size_512_interval_2', content='str'))
        result = self.execute_module()
        self.assertEqual(result['commands'], 'ping 10.10.10.11 count 5 size 512 interval 2')
        self.assertEqual(result['packet_loss'], '0%')
        self.assertEqual(result['packets_rx'], 5)
        self.assertEqual(result['packets_tx'], 5)
        self.assertEqual(result['rtt']['min'], 18.71)
        self.assertEqual(result['rtt']['avg'], 17.87)
        self.assertEqual(result['rtt']['max'], 20.04)
        self.assertEqual(result['rtt']['stddev'], 2.165)
