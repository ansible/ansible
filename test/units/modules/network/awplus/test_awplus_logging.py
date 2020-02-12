#
# (c) 2020 Allied Telesis
# (c) 2017 Paul Neumann
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

import json

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_logging
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusLoggingModule(TestAwplusModule):

    module = awplus_logging

    def setUp(self):
        super(TestAwplusLoggingModule, self).setUp()

        self.mock_run_commands = patch(
            'ansible.modules.network.awplus.awplus_logging.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestAwplusLoggingModule, self).tearDown()

        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module, command = args
            output = list()

            filename = str(command).replace(' ', '_')
            output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_awplus_logging_buffer_size_changed_explicit(self):
        set_module_args(dict(dest='buffered', size=100))
        commands = ['log buffered size 100']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_logging_add_host(self):
        set_module_args(dict(dest='host', name='192.168.1.1'))
        commands = ['log host 192.168.1.1']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_logging_host_idempotent(self):
        set_module_args(dict(dest='console', facility='news'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_awplus_logging_delete_non_exist_host(self):
        set_module_args(dict(dest='host', name='192.168.1.1', state='absent'))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_awplus_logging_delete_host(self):
        set_module_args(dict(dest='host', name='2.3.4.5', state='absent'))
        commands = ['no log host 2.3.4.5']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_logging_configure_disabled_monitor_destination(self):
        set_module_args(dict(dest='monitor', state='absent'))
        commands = ['no log monitor']
        self.execute_module(changed=True, commands=commands)
