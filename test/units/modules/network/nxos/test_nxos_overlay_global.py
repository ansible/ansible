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
from ansible.modules.network.nxos import nxos_overlay_global
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosOverlayGlobalModule(TestNxosModule):

    module = nxos_overlay_global

    def setUp(self):
        super(TestNxosOverlayGlobalModule, self).setUp()
        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_overlay_global.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_overlay_global.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosOverlayGlobalModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('', 'nxos_overlay_global_config.cfg')
        self.load_config.return_value = None

    def test_nxos_overlay_global_up(self):
        set_module_args(dict(anycast_gateway_mac="a.a.a"))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['fabric forwarding anycast-gateway-mac 000A.000A.000A'])
