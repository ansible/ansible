# (c) 2019 Red Hat Inc.
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
from ansible.modules.network.cloudengine import ce_mdn_interface
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_mdn_interface

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_mdn_interface.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_config = patch('ansible.modules.network.cloudengine.ce_mdn_interface.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = "<ok/>"
        self.before = load_fixture('ce_mdn_interface', 'before.txt')
        self.after = load_fixture('ce_mdn_interface', 'after.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_mdn_enable(self):
        update = [['lldp enable', 'interface 10GE1/0/1', 'lldp mdn enable']]
        self.get_nc_config.side_effect = (self.before, self.before, self.after, self.after)
        set_module_args(dict(
            lldpenable='enabled',
            mdnstatus='rxOnly',
            ifname='10GE1/0/1')
        )
        result = self.execute_module(changed=True)
        self.assertEquals(sorted(result['updates']), sorted(update))

    def test_repeat_enable(self):
        self.get_nc_config.side_effect = (self.after, self.after, self.after, self.after, )
        set_module_args(dict(
            lldpenable='enabled',
            mdnstatus='rxOnly',
            ifname='10GE1/0/1')
        )
        self.execute_module(changed=False)
