# (c) 2017 Red Hat Inc.
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

try:
    from lxml.etree import fromstring
except ImportError:
    from xml.etree.ElementTree import fromstring

from units.compat.mock import patch
from ansible.modules.network.junos import junos_command
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule, load_fixture

RPC_CLI_MAP = {
    'get-software-information': 'show version'
}


class TestJunosCommandModule(TestJunosModule):

    module = junos_command

    def setUp(self):
        super(TestJunosCommandModule, self).setUp()

        self.mock_conn = patch('ansible.module_utils.network.junos.junos.Connection')
        self.conn = self.mock_conn.start()

        self.mock_netconf = patch('ansible.module_utils.network.junos.junos.NetconfConnection')
        self.netconf_conn = self.mock_netconf.start()

        self.mock_exec_rpc = patch('ansible.modules.network.junos.junos_command.exec_rpc')
        self.exec_rpc = self.mock_exec_rpc.start()

        self.mock_netconf_rpc = patch('ansible.module_utils.network.common.netconf.NetconfConnection')
        self.netconf_rpc = self.mock_netconf_rpc.start()

        self.mock_get_connection = patch('ansible.modules.network.junos.junos_command.get_connection')
        self.get_connection = self.mock_get_connection.start()

        self.mock_get_capabilities = patch('ansible.modules.network.junos.junos_command.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'network_api': 'netconf'}

    def tearDown(self):
        super(TestJunosCommandModule, self).tearDown()
        self.mock_conn.stop()
        self.mock_netconf.stop()
        self.mock_get_capabilities.stop()
        self.mock_netconf_rpc.stop()
        self.mock_exec_rpc.stop()
        self.mock_get_connection.stop()

    def load_fixtures(self, commands=None, format='text', changed=False):
        def load_from_file(*args, **kwargs):
            element = fromstring(args[1])
            if element.text:
                path = str(element.text)
            else:
                path = RPC_CLI_MAP[str(element.tag)]

            filename = path.replace(' ', '_')
            filename = '%s_%s.txt' % (filename, format)
            return load_fixture(filename)

        self.exec_rpc.side_effect = load_from_file

    def test_junos_command_simple(self):
        set_module_args(dict(commands=['show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname:'))

    def test_junos_command_multiple(self):
        set_module_args(dict(commands=['show version', 'show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Hostname:'))

    def test_junos_command_wait_for(self):
        wait_for = 'result[0] contains "Junos:"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module()

    def test_junos_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.exec_rpc.call_count, 10)

    def test_junos_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for, retries=2))
        self.execute_module(failed=True)
        self.assertEqual(self.exec_rpc.call_count, 2)

    def test_junos_command_match_any(self):
        wait_for = ['result[0] contains "Junos:"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='any'))
        self.execute_module()

    def test_junos_command_match_all(self):
        wait_for = ['result[0] contains "Junos:"',
                    'result[0] contains "JUNOS Software Release"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='all'))
        self.execute_module()

    def test_junos_command_match_all_failure(self):
        wait_for = ['result[0] contains "Junos:"',
                    'result[0] contains "test string"']
        commands = ['show version', 'show version']
        set_module_args(dict(commands=commands, wait_for=wait_for, match='all'))
        self.execute_module(failed=True)

    def test_junos_command_simple_json(self):
        set_module_args(dict(commands=['show version'], display='json'))
        result = self.execute_module(format='json')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue("software-information" in result['stdout'][0])

    def test_junos_command_simple_rpc_text(self):
        set_module_args(dict(rpcs=['get-software-information'], display='text'))
        result = self.execute_module(format='text')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname:'))

    def test_junos_command_simple_rpc_json(self):
        set_module_args(dict(rpcs=['get-software-information'], display='json'))
        result = self.execute_module(format='json')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue("software-information" in result['stdout'][0])
