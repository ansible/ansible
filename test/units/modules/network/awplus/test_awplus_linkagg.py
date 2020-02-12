# (c) 2020 Allied Telesis
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
from ansible.modules.network.awplus import awplus_linkagg
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusLinkaggModule(TestAwplusModule):

    module = awplus_linkagg

    def setUp(self):
        super(TestAwplusLinkaggModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_linkagg.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_linkagg.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestAwplusLinkaggModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture(
            'awplus_linkagg_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_awplus_linkagg_no_change(self):
        set_module_args(dict(group=1, members=["port1.0.2"], mode='active'))
        set_module_args(
            dict(group=2, members=["port1.0.4", 'port1.0.3'], mode='passive'))
        result = self.execute_module(changed=False)
        self.assertEqual([], result['commands'])

    def test_awplus_linkagg_create(self):
        set_module_args(
            dict(group=3, members=["port1.0.2", "port1.0.3"], mode='active'))
        result = self.execute_module(changed=True)
        cmds = [
            'interface port1.0.2', 'channel-group 3 mode active',
            'interface port1.0.3', 'channel-group 3 mode active',
        ]
        self.assertEqual(cmds, result['commands'])

    def test_awplus_linkagg_change(self):
        set_module_args(
            dict(group=3, members=["port1.0.2", "port1.0.4"], mode="passive"))
        result = self.execute_module(changed=True)
        cmds = [
            'interface port1.0.2', 'channel-group 3 mode passive',
            'interface port1.0.4', 'channel-group 3 mode passive'
        ]
        self.assertEqual(cmds, result['commands'])

    def test_awplus_linkagg_remove(self):
        set_module_args(dict(group=2, state="absent"))
        result = self.execute_module(changed=True)
        cmds = [
            'interface port1.0.3', 'no channel-group',
            'interface port1.0.4', 'no channel-group'
        ]
        self.assertEqual(cmds, result['commands'])

    def test_awplus_linkagg_add_member(self):
        set_module_args(
            dict(group=1, members=['port1.0.2', 'port1.0.3'], mode="active"))
        result = self.execute_module(changed=True)
        cmds = [
            'interface port1.0.3', 'channel-group 1 mode active',
        ]
        self.assertEqual(cmds, result['commands'])

    def test_awplus_linkagg_remove_member(self):
        set_module_args(dict(group=2, members=['port1.0.4'], mode="passive"))
        result = self.execute_module(changed=True)
        cmds = [
            'interface port1.0.3', 'no channel-group'
        ]
        self.assertEqual(cmds, result['commands'])
