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

        self.mock_conn = patch('ansible.modules.network.junos.junos_ping.Connection')
        self.conn = self.mock_conn.start()

    def tearDown(self):
        super(TestJunosPingModule, self).tearDown()
        self.mock_conn.stop()

    def load_fixtures(self, commands=None, format=None, changed=None):
        def load_from_file(*args, **kwargs):
            print('Here4')
            command = kwargs['commands']
            output = list()

            filename = str(command).replace(' ', '_')
            output.append(load_fixture('junos_ping_%s' % filename))
            return output

        print('Here1')
        self.conn.side_effect = load_from_file
        # self.conn.get.side_effect = load_from_file

    '''
    def test_junos_ping_expected_success(self):
        # self.conn.get.return_value = load_fixture('junos_ping_ping_10.8.38.39_count_2', content='str')
        # print(self.conn.get.return_value)
        # self.conn.get = MagicMock(return_value=load_fixture('junos_ping_ping_10.8.38.39_count_2', content='str'))
        # print(self.conn.get.return_value)
        set_module_args(dict(count=2, dest="10.8.38.39"))
        self.execute_module()
    '''
