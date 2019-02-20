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

import re
import json

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_lldp
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosLldpModule(TestCnosModule):
    module = cnos_lldp

    def setUp(self):
        super(TestCnosLldpModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.cnos.cnos_lldp.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.cnos.cnos_lldp.load_config'
        )
        self._patch_get_ethernet_range = patch(
            'ansible.modules.network.cnos.cnos_lldp.get_ethernet_range'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()
        self._get_ethernet_range = self._patch_get_ethernet_range.start()

    def tearDown(self):
        super(TestCnosLldpModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()
        self._patch_get_ethernet_range.stop()

    def load_fixtures(self, commands=None):
        config_file = 'cnos_config_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None
        self._get_ethernet_range.return_value = '54'

    def test_cnos_lldp_present(self, *args, **kwargs):
        set_module_args(dict(
            state='present'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface ethernet 1/1-54',
                    'lldp receive',
                    'lldp transmit',
                    'exit',
                    'interface mgmt 0',
                    'lldp receive',
                    'lldp transmit',
                    'exit'
                ],
                'changed': True
            }
        )

    def test_cnos_lldp_absent(self, *args, **kwargs):
        set_module_args(dict(
            state='absent'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface ethernet 1/1-54',
                    'no lldp receive',
                    'no lldp transmit',
                    'exit',
                    'interface mgmt 0',
                    'no lldp receive',
                    'no lldp transmit',
                    'exit'
                ],
                'changed': True
            }
        )
