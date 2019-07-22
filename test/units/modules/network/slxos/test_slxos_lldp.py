#
# (c) 2018 Extreme Networks Inc.
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

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.modules.network.slxos import slxos_lldp
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosLldpModule(TestSlxosModule):
    module = slxos_lldp

    def setUp(self):
        super(TestSlxosLldpModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.slxos.slxos_lldp.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.slxos.slxos_lldp.load_config'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()

    def tearDown(self):
        super(TestSlxosLldpModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'slxos_config_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None

    def test_slxos_lldp_present(self, *args, **kwargs):
        set_module_args(dict(
            state='present'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'protocol lldp',
                    'no disable'
                ],
                'changed': True
            }
        )

    def test_slxos_lldp_absent(self, *args, **kwargs):
        set_module_args(dict(
            state='absent'
        ))
        result = self.execute_module()
        self.assertEqual(
            result,
            {
                'commands': [],
                'changed': False
            }
        )

    def test_slxos_lldp_invalid_argument(self, *args, **kwargs):
        set_module_args(dict(
            state='absent',
            shawshank='Redemption'
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertTrue(re.match(
            r'Unsupported parameters for \((basic.py|basic.pyc)\) module: '
            'shawshank Supported parameters include: state',
            result['msg']
        ), 'Output did not match. Got: %s' % result['msg'])
