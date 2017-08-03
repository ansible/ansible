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
from ansible.modules.network.nxos import nxos_bgp_neighbor
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosBgpNeighborModule(TestNxosModule):

    module = nxos_bgp_neighbor

    def setUp(self):
        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_bgp_neighbor.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_bgp_neighbor.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.get_config.return_value = load_fixture('', 'nxos_bgp_config.cfg')
        self.load_config.return_value = None

    def test_nxos_bgp_neighbor(self):
        set_module_args(dict(asn=65535, neighbor='3.3.3.3', description='some words'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router bgp 65535', 'neighbor 3.3.3.3', 'description some words'])
