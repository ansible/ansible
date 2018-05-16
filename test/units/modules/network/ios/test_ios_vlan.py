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
from ansible.modules.network.ios import ios_vlan
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosUserModule(TestIosModule):

    module = ios_vlan

    def setUp(self):
        super(TestIosUserModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_vlan.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_vlan.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosUserModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('ios_vlan_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_ios_vlan_create(self):
        set_module_args(dict(vlan_id='2', name='test', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 2', 'name test'])