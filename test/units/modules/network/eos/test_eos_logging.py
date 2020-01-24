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

from units.compat.mock import patch
from ansible.modules.network.eos import eos_logging
from units.modules.utils import set_module_args
from .eos_module import TestEosModule, load_fixture


class TestEosLoggingModule(TestEosModule):

    module = eos_logging

    def setUp(self):
        super(TestEosLoggingModule, self).setUp()
        self._log_config = load_fixture('eos_logging_config.cfg')

        self.mock_get_config = patch('ansible.modules.network.eos.eos_logging.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.eos.eos_logging.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestEosLoggingModule, self).tearDown()

        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('eos_logging_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_eos_setup_host_logging_idempotenet(self):
        set_module_args(dict(dest='host', name='175.16.0.10', state='present'))
        self.execute_module(changed=False, commands=[])

    def test_eos_setup_host_logging(self):
        set_module_args(dict(dest='host', name='175.16.0.1', state='present'))
        commands = ['logging host 175.16.0.1']
        self.execute_module(changed=True, commands=commands)

    def test_eos_buffer_size_outofrange(self):
        set_module_args(dict(dest='buffered', size=5))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], "size must be between 10 and 2147483647")

    def test_eos_buffer_size_datatype(self):
        set_module_args(dict(dest='buffered', size='ten'))
        result = self.execute_module(failed=True)
        self.assertIn("we were unable to convert to int", result['msg'])

    def test_eos_buffer_size(self):
        set_module_args(dict(dest='buffered', size=5000))
        commands = ['logging buffered 5000']
        self.execute_module(changed=True, commands=commands)

    def test_eos_buffer_size_idempotent(self):
        set_module_args(dict(dest='buffered', size=50000, level='informational'))
        self.execute_module(changed=False, commands=[])

    def test_eos_facilty(self):
        set_module_args(dict(facility='local2'))
        commands = ['logging facility local2']
        self.execute_module(changed=True, commands=commands)

    def test_eos_facility_idempotent(self):
        set_module_args(dict(facility='local7'))
        self.execute_module(changed=False, commands=[])

    def test_eos_level(self):
        set_module_args(dict(dest='console', level='critical'))
        commands = ['logging console critical']
        self.execute_module(changed=True, commands=commands)

    def test_eos_level_idempotent(self):
        set_module_args(dict(dest='console', level='warnings'))
        self.execute_module(changed=False, commands=[])

    def test_eos_logging_state_absent(self):
        set_module_args(dict(dest='host', name='175.16.0.10', state='absent'))
        commands = ['no logging host 175.16.0.10']
        self.execute_module(changed=True, commands=commands)
