# This file is part of Ansible
#
# Ansible is free softwarei=you can redistribute it and/or modify
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
from ansible.modules.network.ios import ios_acl
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosAclModule(TestIosModule):

    module = ios_acl

    def setUp(self):
        super(TestIosAclModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.ios.ios_acl.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_acl.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosAclModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.run_commands.return_value = load_fixture('ios_acl_config.cfg').strip()
        self.load_config.return_value = dict(diff=None, session='session')

    def test_ios_acl_idempotent(self):
        set_module_args(dict(
            parent="TM_LAN",
            type="extended",
            number="30",
            status="permit",
            protocol="udp",
            source="host 192.168.90.250",
            destination="29.0.0.0 0.0.7.255",
            dst_port="eq syslog",
            logging=True,
            state="present",
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_acl_config(self):
        set_module_args(dict(
            parent="TM_LAN",
            type="extended",
            number="60",
            status="deny",
            protocol="udp",
            source="29.0.0.0 0.0.7.255",
            destination="host 8.8.8.8",
            dst_port="eq domain",
            logging=False,
            state="present",
        ))
        commands = [
            "ip access-list extended MY_TEST",
            "60 deny udp 29.0.0.0 0.0.7.255 host 8.8.8.8 eq domain",
        ]
        self.execute_module(changed=True, commands=commands)

    def test_ios_acl_remove(self):
        set_module_args(dict(
            parent="TM_LAN",
            type="extended",
            number="60",
            status="deny",
            protocol="udp",
            source="29.0.0.0 0.0.7.255",
            destination="host 8.8.8.8",
            dst_port="eq domain",
            logging=False,
            state="absent",
        ))
        commands = [
            "ip access-list extended MY_TEST",
            "no 60 deny udp 29.0.0.0 0.0.7.255 host 8.8.8.8 eq domain",
        ]
        self.execute_module(changed=True, commands=commands)
