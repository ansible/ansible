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
import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_evpn_global
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosEvpnGlobalModule(TestNxosModule):

    module = nxos_evpn_global

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_evpn_global.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_evpn_global.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def start_configured(self, *args, **kwargs):
        self.get_config.return_value = load_fixture('nxos_evpn_global', 'configured.cfg')
        return self.execute_module(*args, **kwargs)

    def start_unconfigured(self, *args, **kwargs):
        self.get_config.return_value = load_fixture('nxos_evpn_global', 'unconfigured.cfg')
        return self.execute_module(*args, **kwargs)

    def test_nxos_evpn_global_enable(self):
        set_module_args(dict(nv_overlay_evpn=True))
        commands = ['nv overlay evpn']
        self.start_unconfigured(changed=True, commands=commands)

    def test_nxos_evpn_global_disable(self):
        set_module_args(dict(nv_overlay_evpn=False))
        commands = ['no nv overlay evpn']
        self.start_configured(changed=True, commands=commands)
