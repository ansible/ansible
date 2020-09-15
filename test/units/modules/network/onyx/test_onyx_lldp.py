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

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_lldp
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxInterfaceModule(TestOnyxModule):

    module = onyx_lldp

    def setUp(self):
        super(TestOnyxInterfaceModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_lldp.OnyxLldpModule, "_get_lldp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        if commands == ['lldp']:
            self.get_config.return_value = None
        else:
            config_file = 'onyx_lldp_show.cfg'
            self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_lldp_no_change(self):
        set_module_args(dict())
        self.execute_module(changed=False)

    def test_lldp_disable(self):
        set_module_args(dict(state='absent'))
        commands = ['no lldp']
        self.execute_module(changed=True, commands=commands)

    def test_lldp_enable(self):
        set_module_args(dict(state='present'))
        commands = ['lldp']
        self.execute_module(changed=True, commands=commands)
