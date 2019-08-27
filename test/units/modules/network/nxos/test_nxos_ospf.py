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
from ansible.modules.network.nxos import nxos_ospf
from .nxos_module import TestNxosModule, set_module_args


class TestNxosOspfModule(TestNxosModule):

    module = nxos_ospf

    def setUp(self):
        super(TestNxosOspfModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_ospf.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_ospf.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosOspfModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_nxos_ospf_present(self):
        set_module_args(dict(ospf=1, state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['router ospf 1'])

    def test_nxos_ospf_absent(self):
        set_module_args(dict(ospf=1, state='absent'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])
