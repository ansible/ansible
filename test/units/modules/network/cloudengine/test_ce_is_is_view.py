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
from ansible.modules.network.cloudengine import ce_is_is_view
from units.modules.network.cloudengine.ce_module import TestCloudEngineModule, load_fixture
from units.modules.utils import set_module_args


class TestCloudEngineLacpModule(TestCloudEngineModule):
    module = ce_is_is_view

    def setUp(self):
        super(TestCloudEngineLacpModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.cloudengine.ce_is_is_view.get_nc_config')
        self.get_nc_config = self.mock_get_config.start()

        self.mock_set_config = patch('ansible.modules.network.cloudengine.ce_is_is_view.set_nc_config')
        self.set_nc_config = self.mock_set_config.start()
        self.set_nc_config.return_value = None

        self.before = load_fixture('ce_is_is_view', 'before.txt')
        self.after = load_fixture('ce_is_is_view', 'after.txt')

    def tearDown(self):
        super(TestCloudEngineLacpModule, self).tearDown()
        self.mock_set_config.stop()
        self.mock_get_config.stop()

    def test_ce_is_is_view_absent(self):
        self.get_nc_config.side_effect = (self.after, self.before)
        config = dict(
            instance_id=100,
            description='ISIS',
            islevel='level_1',
            coststyle='narrow',
            stdlevel2cost=60,
            stdbandwidth=100,
            autocostenable=True,
            autocostenablecompatible=True,
            netentity='netentity',
            preference_value=100,
            route_policy_name='route',
            max_load=32,
            ip_address='1.1.1.1',
            weight=100,
            penetration_direct='level2-level1',
            import_routepolicy_name='import',
            tag=100,
            allow_filter=True,
            allow_up_down=True,
            enablelevel1tolevel2=True,
            defaultmode='always',
            mode_routepolicyname='mode',
            cost=100,
            mode_tag=100,
            level_type='level_1',
            avoid_learning=True,
            protocol='ospf',
            processid=100,
            cost_type='external',
            import_cost=100,
            import_tag=100,
            import_route_policy='import',
            impotr_leveltype='level_1',
            inheritcost=True,
            permitibgp=True,
            export_protocol='ospf',
            export_policytype='aclNumOrName',
            export_processid=100,
            export_ipprefix='export',
            export_routepolicyname='export',
            import_aclnumorname='acl',
            import_routepolicyname='import',
            bfd_min_rx=100,
            bfd_min_tx=100,
            bfd_multiplier_num=10,
            state='absent'
        )
        set_module_args(config)
        self.execute_module(changed=True)

    def test_ce_is_is_view_present(self):
        self.get_nc_config.side_effect = (self.before, self.after)
        update = ['isis 100',
                  'description ISIS',
                  'is-level level_1',
                  'cost-style narrow',
                  'circuit-cost 60 level-2',
                  'bandwidth-reference 100',
                  'network-entity netentity',
                  'preference 100 route-policy route',
                  'maximum load-balancing 32',
                  'nexthop 1.1.1.1 weight 100',
                  'import-route isis level-2 into level-1 filter-policy route-policy import tag 100 direct allow-filter-policy allow-up-down-bit',
                  'preference 100 route-policy route',
                  'undo import-route isis level-1 into level-2 disable',
                  'default-route-advertise always cost 100 tag 100 level-1 avoid-learning',
                  'import-route isis level-2 into level-1 filter-policy route-policy import tag 100 direct allow-filter-policy allow-up-down-bit',
                  'preference 100 route-policy route',
                  'import-route ospf 100 inherit-cost cost-type external cost 100 tag 100 route-policy import level-1',
                  'default-route-advertise always cost 100 tag 100 level-1 avoid-learning',
                  'import-route isis level-2 into level-1 filter-policy route-policy import tag 100 direct allow-filter-policy allow-up-down-bit',
                  'preference 100 route-policy route',
                  'bfd all-interfaces enable',
                  'bfd all-interfaces min-rx-interval 100 min-tx-interval 100 detect-multiplier 10',
                  'import-route ospf 100 inherit-cost cost-type external cost 100 tag 100 route-policy import level-1',
                  'default-route-advertise always cost 100 tag 100 level-1 avoid-learning',
                  'import-route isis level-2 into level-1 filter-policy route-policy import tag 100 direct allow-filter-policy allow-up-down-bit',
                  'preference 100 route-policy route',
                  'filter-policy ip-prefix export route-policy export export ospf 100',
                  'bfd all-interfaces min-rx-interval 100 min-tx-interval 100 detect-multiplier 10',
                  'import-route ospf 100 inherit-cost cost-type external cost 100 tag 100 route-policy import level-1',
                  'default-route-advertise always cost 100 tag 100 level-1 avoid-learning',
                  'import-route isis level-2 into level-1 filter-policy route-policy import tag 100 direct allow-filter-policy allow-up-down-bit',
                  'preference 100 route-policy route',
                  'filter-policy acl-name acl route-policy importimport',
                  'filter-policy ip-prefix export route-policy export export ospf 100',
                  'bfd all-interfaces min-rx-interval 100 min-tx-interval 100 detect-multiplier 10',
                  'import-route ospf 100 inherit-cost cost-type external cost 100 tag 100 route-policy import level-1',
                  'default-route-advertise always cost 100 tag 100 level-1 avoid-learning',
                  'import-route isis level-2 into level-1 filter-policy route-policy import tag 100 direct allow-filter-policy allow-up-down-bit',
                  'preference 100 route-policy route',
                  'auto-cost enable',
                  'auto-cost enable compatible']

        config = dict(
            instance_id=100,
            description='ISIS',
            islevel='level_1',
            coststyle='narrow',
            stdlevel2cost=60,
            stdbandwidth=100,
            autocostenable=True,
            autocostenablecompatible=True,
            netentity='netentity',
            preference_value=100,
            route_policy_name='route',
            max_load=32,
            ip_address='1.1.1.1',
            weight=100,
            penetration_direct='level2-level1',
            import_routepolicy_name='import',
            tag=100,
            allow_filter=True,
            allow_up_down=True,
            enablelevel1tolevel2=True,
            defaultmode='always',
            mode_routepolicyname='mode',
            cost=100,
            mode_tag=100,
            level_type='level_1',
            avoid_learning=True,
            protocol='ospf',
            processid=100,
            cost_type='external',
            import_cost=100,
            import_tag=100,
            import_route_policy='import',
            impotr_leveltype='level_1',
            inheritcost=True,
            permitibgp=True,
            export_protocol='ospf',
            export_policytype='aclNumOrName',
            export_processid=100,
            export_ipprefix='export',
            export_routepolicyname='export',
            import_aclnumorname='acl',
            import_routepolicyname='import',
            bfd_min_rx=100,
            bfd_min_tx=100,
            bfd_multiplier_num=10
        )
        set_module_args(config)
        result = self.execute_module(changed=True)
        self.assertEquals(sorted(result['updates']), sorted(update))

    def test_ce_is_is_view_no_changed(self):
        self.get_nc_config.side_effect = (self.after, self.after)
        config = dict(
            instance_id=100,
            description='ISIS',
            islevel='level_1',
            coststyle='narrow',
            stdlevel2cost=60,
            stdbandwidth=100,
            autocostenable=True,
            autocostenablecompatible=True,
            netentity='netentity',
            preference_value=100,
            route_policy_name='route',
            max_load=32,
            ip_address='1.1.1.1',
            weight=100,
            penetration_direct='level2-level1',
            import_routepolicy_name='import',
            tag=100,
            allow_filter=True,
            allow_up_down=True,
            enablelevel1tolevel2=True,
            defaultmode='always',
            mode_routepolicyname='mode',
            cost=100,
            mode_tag=100,
            level_type='level_1',
            avoid_learning=True,
            protocol='ospf',
            processid=100,
            cost_type='external',
            import_cost=100,
            import_tag=100,
            import_route_policy='import',
            impotr_leveltype='level_1',
            inheritcost=True,
            permitibgp=True,
            export_protocol='ospf',
            export_policytype='aclNumOrName',
            export_processid=100,
            export_ipprefix='export',
            export_routepolicyname='export',
            import_aclnumorname='acl',
            import_routepolicyname='import',
            bfd_min_rx=100,
            bfd_min_tx=100,
            bfd_multiplier_num=10
        )
        set_module_args(config)
        self.execute_module(changed=False)
