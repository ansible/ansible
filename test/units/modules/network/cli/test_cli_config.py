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
from ansible.modules.network.cli import cli_config
from units.modules.utils import set_module_args
from .cli_module import TestCliModule


class TestCliConfigModule(TestCliModule):

    module = cli_config

    def setUp(self):
        super(TestCliConfigModule, self).setUp()

        self.mock_connection = patch('ansible.modules.network.cli.cli_config.Connection')
        self.get_connection = self.mock_connection.start()

        self.conn = self.get_connection()

    def tearDown(self):
        super(TestCliConfigModule, self).tearDown()

        self.mock_connection.stop()

    @patch('ansible.modules.network.cli.cli_config.run')
    def test_cli_config_backup_returns__backup__(self, run_mock):
        self.conn.get_capabilities = MagicMock(return_value='{}')

        args = dict(backup=True)
        set_module_args(args)

        run_mock.return_value = {}

        result = self.execute_module()
        self.assertIn('__backup__', result)
