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
from ansible.modules.network.ios import ios_ntp
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosNtpModule(TestIosModule):

    module = ios_ntp

    def setUp(self):
        super(TestIosNtpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_ntp.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_ntp.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosNtpModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_ntp_config.cfg').strip()
        self.load_config.return_value = dict(diff=None, session='session')

    def test_ios_ntp_idempotent(self):
        set_module_args(dict(
            server='10.75.32.5',
            source_int='Loopback0',
            acl='NTP_ACL',
            logging=True,
            auth=True,
            auth_key='15435A030726242723273C21181319000A',
            key_id='10',
            state='present'
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_ios_ntp_config(self):
        set_module_args(dict(
            server='10.75.33.5',
            source_int='Vlan2',
            acl='NTP_ACL',
            logging=True,
            auth=True,
            auth_key='15435A030726242723273C21181319000A',
            key_id='10',
            state='present'
        ))
        commands = [
            'ntp server 10.75.33.5',
            'ntp source Vlan2'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_ios_ntp_remove(self):
        set_module_args(dict(
            server='10.75.32.5',
            source_int='Loopback0',
            acl='NTP_ACL',
            logging=True,
            auth=True,
            auth_key='15435A030726242723273C21181319000A',
            key_id='10',
            state='absent'
        ))
        commands = [
            'no ntp server 10.75.32.5',
            'no ntp source Loopback0',
            'no ntp access-group peer NTP_ACL',
            'no ntp logging',
            'no ntp authenticate',
            'no ntp trusted-key 10',
            'no ntp authentication-key 10 md5 15435A030726242723273C21181319000A 7'
        ]
        self.execute_module(changed=True, commands=commands)
