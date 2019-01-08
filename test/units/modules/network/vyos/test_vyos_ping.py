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

from units.compat.mock import patch
from ansible.modules.network.vyos import vyos_ping
from units.modules.utils import set_module_args
from .vyos_module import TestVyosModule, load_fixture


class TestVyosPingModule(TestVyosModule):

    module = vyos_ping

    def setUp(self):
        super(TestVyosPingModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.vyos.vyos_ping.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestVyosPingModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('vyos_ping_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_vyos_ping_expected_success(self):
        ''' Test for successful pings when destination should be reachable '''
        set_module_args(dict(count=2, dest="10.10.10.10"))
        self.execute_module()

    def test_vyos_ping_expected_failure(self):
        ''' Test for unsuccessful pings when destination should not be reachable '''
        set_module_args(dict(count=4, dest="10.10.10.20", state="absent"))
        self.execute_module()

    def test_vyos_ping_unexpected_success(self):
        ''' Test for successful pings when destination should not be reachable - FAIL. '''
        set_module_args(dict(count=2, dest="10.10.10.10", state="absent"))
        self.execute_module(failed=True)

    def test_vyos_ping_unexpected_failure(self):
        ''' Test for unsuccessful pings when destination should be reachable - FAIL. '''
        set_module_args(dict(count=4, dest="10.10.10.20"))
        self.execute_module(failed=True)

    def test_vyos_ping_failure_stats(self):
        '''Test for asserting stats when ping fails'''
        set_module_args(dict(count=4, dest="10.10.10.20"))
        result = self.execute_module(failed=True)
        self.assertEqual(result['packet_loss'], '100%')
        self.assertEqual(result['packets_rx'], 0)
        self.assertEqual(result['packets_tx'], 4)

    def test_vyos_ping_success_stats(self):
        '''Test for asserting stats when ping passes'''
        set_module_args(dict(count=2, dest="10.10.10.10"))
        result = self.execute_module()
        self.assertEqual(result['packet_loss'], '0%')
        self.assertEqual(result['packets_rx'], 2)
        self.assertEqual(result['packets_tx'], 2)
        self.assertEqual(result['rtt']['min'], 12)
        self.assertEqual(result['rtt']['avg'], 17)
        self.assertEqual(result['rtt']['max'], 22)
        self.assertEqual(result['rtt']['mdev'], 10)

    def test_vyos_ping_success_stats_with_options(self):
        set_module_args(dict(count=10, ttl=128, size=512, dest="10.10.10.11"))
        result = self.execute_module()
        self.assertEqual(result['packet_loss'], '0%')
        self.assertEqual(result['packets_rx'], 10)
        self.assertEqual(result['packets_tx'], 10)
        self.assertEqual(result['rtt']['min'], 1)
        self.assertEqual(result['rtt']['avg'], 3)
        self.assertEqual(result['rtt']['max'], 21)
        self.assertEqual(result['rtt']['mdev'], 5)
