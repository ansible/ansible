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
from ansible.modules.network.junos import junos_rpc
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule, load_fixture


RPC_CLI_MAP = {
    'get-software-information': 'show version',
    'get-interface-information': 'show interfaces details',
    'get-system-memory-information': 'show system memory',
    'get-chassis-inventory': 'show chassis hardware',
    'get-system-storage': 'show system storage',
    'load-configuration': 'load configuration'
}


class TestJunosCommandModule(TestJunosModule):

    module = junos_rpc

    def setUp(self):
        super(TestJunosCommandModule, self).setUp()
        self.mock_conn = patch('ansible.module_utils.connection.Connection')
        self.conn = self.mock_conn.start()

        self.mock_netconf = patch('ansible.module_utils.network.junos.junos.NetconfConnection')
        self.netconf_conn = self.mock_netconf.start()

        self.mock_netconf_rpc = patch('ansible.module_utils.network.common.netconf.NetconfConnection')
        self.netconf_rpc = self.mock_netconf_rpc.start()

        self.mock_exec_rpc = patch('ansible.modules.network.junos.junos_rpc.exec_rpc')
        self.exec_rpc = self.mock_exec_rpc.start()

    def tearDown(self):
        super(TestJunosCommandModule, self).tearDown()
        self.mock_conn.stop()
        self.mock_netconf.stop()
        self.mock_netconf_rpc.stop()
        self.mock_exec_rpc.stop()

    def load_fixtures(self, commands=None, format='text', changed=False):
        def load_from_file(*args, **kwargs):
            element = fromstring(args[1])
            if element.text:
                path = str(element.text)
            else:
                tag = str(element.tag)
                if tag.startswith('{'):
                    tag = tag.split('}', 1)[1]
                path = RPC_CLI_MAP[tag]

            filename = path.replace(' ', '_')
            filename = '%s_%s.txt' % (filename, format)

            return load_fixture(filename)

        self.exec_rpc.side_effect = load_from_file

    def test_junos_rpc_xml(self):
        set_module_args(dict(rpc='get-chassis-inventory'))
        result = self.execute_module(format='xml')
        self.assertTrue(result['xml'].find('<chassis-inventory>\n'))

    def test_junos_rpc_text(self):
        set_module_args(dict(rpc='get-software-information', output='text'))
        result = self.execute_module(format='text')
        self.assertTrue(result['output_lines'][0].startswith('Hostname: vsrx01'))

    def test_junos_rpc_json(self):
        set_module_args(dict(rpc='get-software-information', output='json'))
        result = self.execute_module(format='json')
        self.assertTrue('software-information' in result['output'])

    def test_junos_rpc_args(self):
        set_module_args(dict(rpc='get-software-information', args={'interface': 'em0', 'media': True}))
        result = self.execute_module(format='xml')
        args, kwargs = self.exec_rpc.call_args
        reply = args[1]
        self.assertTrue(reply.find('<interface>em0</interface><media /></get-software-information>'))

    def test_junos_rpc_attrs(self):
        set_module_args(dict(rpc='load-configuration', output='xml', attrs={'url': '/var/tmp/config.conf'}))
        result = self.execute_module(format='xml')
        self.assertTrue(result['xml'].find('<load-success/>'))
