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
from ansible.modules.network.ios import ios_pmtud
from .ios_module import TestIosModule, load_fixture, set_module_args


class TestIosPmtudModule(TestIosModule):
    ''' Class used for Unit Tests against ios_pmtud module '''
    module = ios_pmtud

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.ios.ios_pmtud.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        # path MTU discovery is interactive
        pass

    def test_ios_pmtud_expected_success(self):
        ''' Test path MTU discovery when destination should be reachable '''
        set_module_args(dict(dest="8.8.8.8"))
        self.execute_module()

    def test_ios_pmtud_expected_success2(self):
        ''' Test path MTU discovery with a valid max_range '''
        set_module_args(dict(dest="8.8.8.8", max_range=2))
        self.execute_module()

    def test_ios_pmtud_expected_success3(self):
        ''' Test path MTU discovery with a valid max_range '''
        set_module_args(dict(dest="8.8.8.8", max_range=512))
        self.execute_module()

    def test_ios_pmtud_expected_success4(self):
        ''' Test path MTU discovery with a valid max_range '''
        set_module_args(dict(dest="8.8.8.8", max_range=1024))
        self.execute_module()

    def test_ios_pmtud_expected_success5(self):
        ''' Test path MTU discovery with invalid max_range '''
        set_module_args(dict(dest="8.8.8.8", max_range=100))
        self.execute_module()

    def test_ios_pmtud_expected_success6(self):
        ''' Test path MTU discovery with invalid max_range '''
        set_module_args(dict(dest="8.8.8.8", max_range=1042))
        self.execute_module()
