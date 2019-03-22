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

from units.compat.mock import patch
from ansible.modules.network.junos import junos_netconf
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule


class TestJunosCommandModule(TestJunosModule):

    module = junos_netconf

    def setUp(self):
        super(TestJunosCommandModule, self).setUp()

        self.mock_lock_configuration = patch('ansible.module_utils.network.junos.junos.lock_configuration')
        self.lock_configuration = self.mock_lock_configuration.start()

        self.mock_unlock_configuration = patch('ansible.module_utils.network.junos.junos.unlock_configuration')
        self.unlock_configuration = self.mock_unlock_configuration.start()

        self.mock_commit_configuration = patch('ansible.modules.network.junos.junos_netconf.commit_configuration')
        self.commit_configuration = self.mock_commit_configuration.start()

        self.mock_conn = patch('ansible.module_utils.connection.Connection')
        self.conn = self.mock_conn.start()

        self.mock_netconf = patch('ansible.module_utils.network.junos.junos.NetconfConnection')
        self.netconf_conn = self.mock_netconf.start()

        self.mock_netconf_rpc = patch('ansible.module_utils.network.common.netconf.NetconfConnection')
        self.netconf_rpc = self.mock_netconf_rpc.start()

        self.mock_get_capabilities = patch('ansible.module_utils.network.junos.junos.get_capabilities')
        self.get_capabilities = self.mock_get_capabilities.start()
        self.get_capabilities.return_value = {'network_api': 'netconf'}

    def tearDown(self):
        super(TestJunosCommandModule, self).tearDown()
        self.mock_lock_configuration.stop()
        self.mock_unlock_configuration.stop()
        self.mock_commit_configuration.stop()
        self.mock_conn.stop()
        self.mock_netconf.stop()
        self.mock_netconf_rpc.stop()
        self.mock_get_capabilities.stop()

    def test_junos_netconf_enable(self):
        self.netconf_conn().get.return_value = ''
        set_module_args(dict(state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system services netconf ssh port 830'])

    def test_junos_netconf_disable(self):
        out = '''
              ssh {
                port 830;
                }
            '''
        self.netconf_conn().get.return_value = out
        set_module_args(dict(state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['delete system services netconf'])

    def test_junos_netconf_port_change(self):
        out = '''
              ssh {
                port 830;
                }
            '''
        self.netconf_conn().get.return_value = out
        set_module_args(dict(state='present', netconf_port=22))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system services netconf ssh port 22'])

    def test_junos_netconf_port_error(self):
        out = '''
              ssh {
                port 22;
                }
            '''
        self.netconf_conn().get.return_value = out
        set_module_args(dict(state='present', netconf_port=0))
        result = self.execute_module(changed=True, failed=True)
        self.assertEqual(result['msg'], 'netconf_port must be between 1 and 65535')

    def test_junos_netconf_config_error(self):
        self.netconf_conn().get.return_value = None
        set_module_args(dict(state='present'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'unable to retrieve current config')
