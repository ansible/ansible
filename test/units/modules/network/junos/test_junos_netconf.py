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

from ansible.compat.tests.mock import patch
from ansible.modules.network.junos import junos_netconf
from .junos_module import TestJunosModule, set_module_args


class TestJunosCommandModule(TestJunosModule):

    module = junos_netconf

    def setUp(self):
        self.mock_exec_command = patch('ansible.modules.network.junos.junos_netconf.exec_command')
        self.exec_command = self.mock_exec_command.start()

        self.mock_lock_configuration = patch('ansible.module_utils.junos.lock_configuration')
        self.lock_configuration = self.mock_lock_configuration.start()

        self.mock_unlock_configuration = patch('ansible.module_utils.junos.unlock_configuration')
        self.unlock_configuration = self.mock_unlock_configuration.start()

        self.mock_commit_configuration = patch('ansible.modules.network.junos.junos_netconf.commit_configuration')
        self.commit_configuration = self.mock_commit_configuration.start()

    def tearDown(self):
        self.mock_exec_command.stop()
        self.mock_lock_configuration.stop()
        self.mock_unlock_configuration.stop()
        self.mock_commit_configuration.stop()

    def test_junos_netconf_enable(self):
        self.exec_command.return_value = 0, '', None
        set_module_args(dict(state='present'))
        result = self.execute_module()
        self.assertEqual(result['commands'], ['set system services netconf ssh port 830'])

    def test_junos_netconf_disable(self):
        out = '''
              ssh {
                port 830;
                }
            '''
        self.exec_command.return_value = 0, out, None
        set_module_args(dict(state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['delete system services netconf'])

    def test_junos_netconf_port_change(self):
        out = '''
              ssh {
                port 830;
                }
            '''
        self.exec_command.return_value = 0, out, None
        set_module_args(dict(state='present', netconf_port=22))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['set system services netconf ssh port 22'])

    def test_junos_netconf_port_error(self):
        out = '''
              ssh {
                port 22;
                }
            '''
        self.exec_command.return_value = 0, out, None
        set_module_args(dict(state='present', netconf_port=0))
        result = self.execute_module(changed=True, failed=True)
        self.assertEqual(result['msg'], 'netconf_port must be between 1 and 65535')

    def test_junos_netconf_config_error(self):
        self.exec_command.return_value = 1, None, None
        set_module_args(dict(state='present'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'unable to retrieve current config')
