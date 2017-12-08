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

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_ospf_vrf
from .nxos_module import TestNxosModule, set_module_args


class TestNxosOspfVrfModule(TestNxosModule):

    module = nxos_ospf_vrf

    def setUp(self):
        super(TestNxosOspfVrfModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_ospf_vrf.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_ospf_vrf.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosOspfVrfModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_nxos_ospf_vrf_present(self):
        set_module_args(dict(ospf=1,
                             vrf='test',
                             timer_throttle_spf_start=50,
                             timer_throttle_spf_hold=1000,
                             timer_throttle_spf_max=2000,
                             timer_throttle_lsa_start=60,
                             timer_throttle_lsa_hold=1100,
                             timer_throttle_lsa_max=3000,
                             state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(sorted(result['commands']),
                         sorted(['router ospf 1',
                                 'vrf test',
                                 'timers throttle lsa 60 1100 3000',
                                 'timers throttle spf 50 1000 2000',
                                 'vrf test']))

    def test_nxos_ospf_vrf_absent(self):
        set_module_args(dict(ospf=1, vrf='test', state='absent'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])
