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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_feature
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosFeatureModule(TestNxosModule):

    module = nxos_feature

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_feature.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_feature.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_feature.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_run_commands.stop()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('nxos_feature.cfg')
        self.load_config.return_value = None

    #def start_configured(self, *args, **kwargs):
    #    self.get_config.return_value = load_fixture('nxos_feature/configured.cfg')
    #    return self.execute_module(*args, **kwargs)

    #def start_unconfigured(self, *args, **kwargs):
    #    self.get_config.return_value = load_fixture('nxos_feature/unconfigured.cfg')
    #    return self.execute_module(*args, **kwargs)

    def test_nxos_feature_enable(self):
        set_module_args(dict(feature='evpn', state='enabled'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [])

    #def test_nxos_feature_disable(self):
    #    set_module_args(dict(feature='evpn', state='disabled'))
    #    result = self.execute_module(changed=True)
    #    self.assertEqual(result['commands'], [])
