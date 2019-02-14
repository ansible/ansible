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
from ansible.modules.network.iosxr import iosxr_netconf
from units.modules.utils import set_module_args
from .iosxr_module import TestIosxrModule


class TestIosxrNetconfModule(TestIosxrModule):

    module = iosxr_netconf

    def setUp(self):
        super(TestIosxrNetconfModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.iosxr.iosxr_netconf.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.iosxr.iosxr_netconf.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosxrNetconfModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def test_iosxr_disable_netconf_service(self):
        self.get_config.return_value = '''
        netconf-yang agent
            ssh
        !
        ssh server netconf vrf default
        '''
        self.load_config.return_value = 'dummy diff'
        set_module_args(dict(netconf_port=830, netconf_vrf='default', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no netconf-yang agent ssh', 'no ssh server netconf port 830', 'no ssh server netconf vrf default'])

    def test_iosxr_enable_netconf_service(self):
        self.get_config.return_value = ''
        self.load_config.return_value = 'dummy diff'
        set_module_args(dict(netconf_port=830, netconf_vrf='default', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['netconf-yang agent ssh', 'ssh server netconf port 830', 'ssh server netconf vrf default'])

    def test_iosxr_change_netconf_port(self):
        self.get_config.return_value = '''
        netconf-yang agent
            ssh
        !
        ssh server netconf vrf default
        '''
        self.load_config.return_value = 'dummy diff'
        set_module_args(dict(netconf_port=9000, state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['ssh server netconf port 9000'])

    def test_iosxr_change_netconf_vrf(self):
        self.get_config.return_value = '''
        netconf-yang agent
            ssh
        !
        ssh server netconf vrf default
        '''
        self.load_config.return_value = 'dummy diff'
        set_module_args(dict(netconf_vrf='new_default', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['ssh server netconf vrf new_default'])
