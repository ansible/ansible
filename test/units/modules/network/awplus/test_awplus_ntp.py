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
from ansible.modules.network.awplus import awplus_ntp
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusNtpModule(TestAwplusModule):

    module = awplus_ntp

    def setUp(self):
        super(TestAwplusNtpModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_ntp.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_ntp.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestAwplusNtpModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture(
            'awplus_ntp_config.cfg').strip()
        self.load_config.return_value = dict(diff=None, session='session')

    def test_awplus_ntp_idempotent(self):
        set_module_args(dict(
            server='10.75.33.5',
            source_int='192.66.44.33',
            restrict='192.155.56.4 allow',
            auth_key='fdasgf',
            key_id='8900',
            state='present'
        ))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_awplus_ntp_config(self):
        set_module_args(dict(
            server='10.75.33.4',
            source_int='192.66.44.32',
            restrict='192.155.56.3 allow',
            auth_key='fdasgg',
            key_id='8901',
            state='present'
        ))
        commands = [
            'ntp server 10.75.33.4',
            'ntp source 192.66.44.32',
            'ntp restrict 192.155.56.3 allow',
            'ntp authentication-key 8901 md5 fdasgg'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_awplus_ntp_remove(self):
        set_module_args(dict(
            server='10.75.33.5',
            source_int='192.66.44.33',
            restrict='192.155.56.4 allow',
            auth_key='fdasgf',
            key_id='8900',
            state='absent'
        ))
        commands = [
            'no ntp server 10.75.33.5',
            'no ntp source',
            'no ntp restrict 192.155.56.4 allow',
            'no ntp authentication-key 8900 md5 fdasgf'
        ]
        self.execute_module(changed=True, commands=commands)
