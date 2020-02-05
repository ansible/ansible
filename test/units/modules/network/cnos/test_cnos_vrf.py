#
# (c) 2019 Lenovo.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_vrf
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosVrfModule(TestCnosModule):

    module = cnos_vrf

    def setUp(self):
        super(TestCnosVrfModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_vrf.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.cnos.cnos_vrf.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self._patch_is_switchport = patch(
            'ansible.modules.network.cnos.cnos_vrf.is_switchport'
        )
        self._is_switchport = self._patch_is_switchport.start()

    def tearDown(self):
        super(TestCnosVrfModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()
        self._patch_is_switchport.stop()

    def load_fixtures(self, commands=None):
        config_file = 'cnos_vrf_config.cfg'
        self.load_config.return_value = load_fixture(config_file)
        self.run_commands.return_value = load_fixture(config_file)
        self._is_switchport.return_value = False

    def test_cnos_vrf_present(self):
        set_module_args(dict(name='test1', state='present'))
        self.execute_module(changed=True, commands=['vrf context test1'])

    def test_cnos_vrf_present_management(self):
        set_module_args(dict(name='management', state='present'))
        self.execute_module(changed=True, commands=['vrf context management'])

    def test_cnos_vrf_absent_management(self):
        set_module_args(dict(name='management', state='absent'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Management VRF context cannot be deleted')

    def test_cnos_vrf_absent_no_change(self):
        set_module_args(dict(name='test1', state='absent'))
        self.execute_module(changed=False, commands=[])

    def test_cnos_vrf_default(self):
        set_module_args(dict(name='default', state='present'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'VRF context default is reserved')
