#
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

from ansible.compat.tests.mock import patch
from ansible.modules.network.ios import ios_ping
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosPingModule(TestIosModule):
    ''' Class used for Unit Tests agains ios_ping module '''
    module = ios_ping

    def setUp(self):
        super(TestIosPingModule, self).setUp()
        self.mock_run_commands = patch('ansible.modules.network.ios.ios_ping.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestIosPingModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module = args
            commands = kwargs['commands']
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('ios_ping_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_ios_ping_expected_success(self):
        ''' Test for successful pings when destination should be reachable '''
        set_module_args(dict(count=2, dest="8.8.8.8"))
        self.execute_module()

    def test_ios_ping_expected_failure(self):
        ''' Test for unsuccessful pings when destination should not be reachable '''
        set_module_args(dict(count=2, dest="10.255.255.250", state="absent", timeout=45))
        self.execute_module()

    def test_ios_ping_unexpected_success(self):
        ''' Test for successful pings when destination should not be reachable - FAIL. '''
        set_module_args(dict(count=2, dest="8.8.8.8", state="absent"))
        self.execute_module(failed=True)

    def test_ios_ping_unexpected_failure(self):
        ''' Test for unsuccessful pings when destination should be reachable - FAIL. '''
        set_module_args(dict(count=2, dest="10.255.255.250", timeout=45))
        self.execute_module(failed=True)
