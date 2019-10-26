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
from ansible.modules.network.cloudengine import ce_multicast_igmp_enable
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_multicast_igmp_enable

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_multicast_igmp_enable.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_config = patch('ansible.modules.network.cloudengine.ce_multicast_igmp_enable.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = "<ok/>"
        self.before = load_fixture('ce_multicast_igmp_enable', 'before.txt')
        self.after = load_fixture('ce_multicast_igmp_enable', 'after.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_igmp_enable(self):
        update = ['igmp snooping enable',
                  'igmp snooping version 2',
                  'igmp snooping proxy']
        self.get_nc_config.side_effect = (self.before, self.after)
        set_module_args(dict(
            aftype='v4',
            features='vlan',
            vlan_id=1,
            igmp=True,
            version=2,
            proxy=True)
        )
        result = self.execute_module(changed=True)
        self.assertEquals(sorted(result['updates']), sorted(update))

    def test_igmp_undo_enable(self):
        update = ['undo igmp snooping enable',
                  'undo igmp snooping version',
                  'undo igmp snooping proxy']
        self.get_nc_config.side_effect = (self.after, self.before)
        set_module_args(dict(
            aftype='v4',
            features='vlan',
            vlan_id=1,
            igmp=True,
            version=2,
            proxy=True,
            state='absent')
        )
        result = self.execute_module(changed=True)
        self.assertEquals(sorted(result['updates']), sorted(update))
