#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_static_route
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxStaticRouteModule(TestOnyxModule):

    module = onyx_static_route

    def setUp(self):
        self.enabled = False
        super(TestOnyxStaticRouteModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_static_route.OnyxStaticRouteModule, "_get_routing_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxStaticRouteModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_static_route.cfg'
        data = load_fixture(config_file)
        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_new_route(self):
        set_module_args(dict(route_type="default", network_prefix='8.8.8.8', netmask='/16', nexthop='10.7.144.58'))
        commands = ['ip route 8.8.8.8 /16 10.7.144.58']
        self.execute_module(changed=True, commands=commands)

    def test_new_mroute(self):
        set_module_args(dict(route_type="multicast", network_prefix='8.8.8.8', netmask='/16', nexthop='10.7.144.58'))
        commands = ['ip mroute 8.8.8.8 /16 10.7.144.58']
        self.execute_module(changed=True, commands=commands)

    def test_new_mroute_vrf(self):
        set_module_args(dict(route_type="multicast", vrf_name='vrf2', network_prefix='8.8.8.8', netmask='/16', nexthop='10.7.144.58'))
        commands = ['ip mroute vrf vrf2 8.8.8.8 /16 10.7.144.58']
        self.execute_module(changed=True, commands=commands)

    def test_change_new_mroute(self):
        set_module_args(dict(route_type="multicast", vrf_name='default', network_prefix='10.7.144.0', netmask='/21', nexthop='10.7.144.58'))
        commands = ['ip mroute vrf default 10.7.144.0 /21 10.7.144.58']
        self.execute_module(changed=True, commands=commands)

    def test_with_distance_route(self):
        set_module_args(dict(route_type="default", network_prefix='8.8.8.8', netmask='/16', nexthop='10.7.144.58', route_distance=5))
        commands = ['ip route 8.8.8.8 /16 10.7.144.58 5']
        self.execute_module(changed=True, commands=commands)

    def test_change_map_hostname(self):
        set_module_args(dict(hostname_map=True))
        commands = ['ip map-hostname']
        self.execute_module(changed=True, commands=commands)

    def test_new_hostname(self):
        set_module_args(dict(hostname='test', hostip='8.8.8.8'))
        commands = ['ip host test 8.8.8.8']
        self.execute_module(changed=True, commands=commands)

    def test_delete_hostname(self):
        set_module_args(dict(hostname_remove=True, hostname='localhost', hostip='10.7.144.144'))
        commands = ['no ip host localhost 10.7.144.144']
        self.execute_module(changed=True, commands=commands)

    def test_multicasting_enable(self):
        set_module_args(dict(multicasting=True, vrf_name='vrf1'))
        commands = ['ip multicast-routing vrf vrf1']
        self.execute_module(changed=True, commands=commands)

    def test_multicasting_disable(self):
        set_module_args(dict(multicasting=False, vrf_name='default'))
        commands = ['no ip multicast-routing vrf default']
        self.execute_module(changed=True, commands=commands)

    def test_routing_enable(self):
        set_module_args(dict(routing=True, vrf_name='vrf1'))
        commands = ['ip routing vrf vrf1']
        self.execute_module(changed=True, commands=commands)

    def test_routing_disable(self):
        set_module_args(dict(routing=False, vrf_name='default'))
        commands = ['no ip routing vrf default']
        self.execute_module(changed=True, commands=commands)

    def test_add_domain(self):
        set_module_args(dict(domain='test'))
        commands = ['ip domain-list test']
        self.execute_module(changed=True, commands=commands)

    def test_remove_domaine(self):
        set_module_args(dict(domain_remove=True, domain='mydomain2'))
        commands = ['no ip domain-list mydomain2']
        self.execute_module(changed=True, commands=commands)

    ''' no change '''
    def test_no_change_map_hostname(self):
        set_module_args(dict(hostname_map=False))
        self.execute_module(changed=False)

    def test_no_change_hostname(self):
        set_module_args(dict(hostname='localhost', hostip='10.7.144.144'))
        self.execute_module(changed=False)

    def test_delete_hostname_no_change(self):
        set_module_args(dict(hostname_remove=True, hostname='localhost', hostip='10.7.144.145'))
        self.execute_module(changed=False)

    def test_multicasting_disable_no_change(self):
        set_module_args(dict(multicasting=False, vrf_name='vrf2'))
        self.execute_module(changed=False)

    def test_routing_enable_no_change(self):
        set_module_args(dict(routing=True, vrf_name='vrf2'))
        self.execute_module(changed=False)

    def test_domain_no_change(self):
        set_module_args(dict(domain='mydomain'))
        self.execute_module(changed=False)

    def test_remove_domain_no_change(self):
        set_module_args(dict(domain_remove=True, domain='mydomain3'))
        self.execute_module(changed=False)
