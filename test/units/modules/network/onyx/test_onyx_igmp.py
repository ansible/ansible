#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_igmp
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxIgmpModule(TestOnyxModule):

    module = onyx_igmp
    enabled = False

    def setUp(self):
        self.enabled = False
        super(TestOnyxIgmpModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_igmp.OnyxIgmpModule, "_show_igmp")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxIgmpModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_igmp_show.cfg'
        data = load_fixture(config_file)
        if self.enabled:
            data[0]['IGMP snooping globally'] = 'enabled'
        self.get_config.return_value = data
        self.load_config.return_value = None

    def test_igmp_no_change(self):
        set_module_args(dict(state='disabled'))
        self.execute_module(changed=False)

    def test_igmp_enable(self):
        set_module_args(dict(state='enabled'))
        commands = ['ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_last_member_query_interval(self):
        set_module_args(dict(state='enabled',
                             last_member_query_interval=10))
        commands = ['ip igmp snooping',
                    'ip igmp snooping last-member-query-interval 10']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_mrouter_timeout(self):
        set_module_args(dict(state='enabled',
                             mrouter_timeout=100))
        commands = ['ip igmp snooping',
                    'ip igmp snooping mrouter-timeout 100']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_port_purge_timeout(self):
        set_module_args(dict(state='enabled',
                             port_purge_timeout=150))
        commands = ['ip igmp snooping',
                    'ip igmp snooping port-purge-timeout 150']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_report_suppression_interval(self):
        set_module_args(dict(state='enabled',
                             report_suppression_interval=10))
        commands = ['ip igmp snooping',
                    'ip igmp snooping report-suppression-interval 10']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_proxy_reporting_disabled(self):
        set_module_args(dict(state='enabled',
                             proxy_reporting='disabled'))
        commands = ['ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_proxy_reporting_enabled(self):
        set_module_args(dict(state='enabled',
                             proxy_reporting='enabled'))
        commands = ['ip igmp snooping',
                    'ip igmp snooping proxy reporting']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_unregistered_multicast_flood(self):
        set_module_args(dict(state='enabled',
                             unregistered_multicast='flood'))
        commands = ['ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_unregistered_multicast_forward(self):
        set_module_args(
            dict(state='enabled',
                 unregistered_multicast='forward-to-mrouter-ports'))
        commands = [
            'ip igmp snooping',
            'ip igmp snooping unregistered multicast forward-to-mrouter-ports'
        ]
        self.execute_module(changed=True, commands=commands)

    def test_igmp_version_v2(self):
        set_module_args(dict(state='enabled',
                             default_version='V2'))
        commands = ['ip igmp snooping',
                    'ip igmp snooping version 2']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_version_v3(self):
        set_module_args(dict(state='enabled',
                             default_version='V3'))
        commands = ['ip igmp snooping']
        self.execute_module(changed=True, commands=commands)

    def test_igmp_disable(self):
        self.enabled = True
        set_module_args(dict(state='disabled'))
        commands = ['no ip igmp snooping']
        self.execute_module(changed=True, commands=commands)
