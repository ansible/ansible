#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_bfd
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxBFDModule(TestOnyxModule):

    module = onyx_bfd

    def setUp(self):
        self.enabled = False
        super(TestOnyxBFDModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_bfd.OnyxBFDModule, "_show_bfd_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxBFDModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_bfd.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_bfd_shutdown_no_change(self):
        set_module_args(dict(shutdown=True))
        self.execute_module(changed=False)

    def test_bfd_shutdown_with_change(self):
        set_module_args(dict(shutdown=False))
        commands = ['no ip bfd shutdown']
        self.execute_module(changed=True, commands=commands)

    def test_vrf_bfd_shutdown_no_change(self):
        set_module_args(dict(shutdown=False,
                             vrf='3'))
        self.execute_module(changed=False)

    def test_vrf_bfd_shutdown_with_change(self):
        set_module_args(dict(shutdown=True,
                             vrf='3'))
        commands = ['ip bfd shutdown vrf 3']
        self.execute_module(changed=True, commands=commands)

    def test_bfd_interval_no_change(self):
        set_module_args(dict(interval_min_rx=50,
                             interval_multiplier=7,
                             interval_transmit_rate=55))
        self.execute_module(changed=False)

    def test_bfd_interval_with_change(self):
        set_module_args(dict(interval_min_rx=55,
                             interval_multiplier=7,
                             interval_transmit_rate=100))
        commands = ['ip bfd interval min-rx 55 multiplier 7 transmit-rate 100 force']
        self.execute_module(changed=True, commands=commands)

    def test_vrf_bfd_interval_no_change(self):
        set_module_args(dict(interval_min_rx=50,
                             interval_multiplier=7,
                             interval_transmit_rate=55,
                             vrf='3'))
        self.execute_module(changed=False)

    def test_vrf_bfd_interval_with_change(self):
        set_module_args(dict(interval_min_rx=55,
                             interval_multiplier=7,
                             interval_transmit_rate=100,
                             vrf='3'))
        commands = ['ip bfd vrf 3 interval min-rx 55 multiplier 7 transmit-rate 100 force']
        self.execute_module(changed=True, commands=commands)

    def test_bfd_iproute_no_change(self):
        set_module_args(dict(iproute_network_prefix='1.1.1.0',
                             iproute_mask_length=24,
                             iproute_next_hop='3.2.2.2'))
        self.execute_module(changed=False)

    def test_bfd_iproute_with_change(self):
        set_module_args(dict(iproute_network_prefix='1.1.1.0',
                             iproute_mask_length=24,
                             iproute_next_hop='3.2.2.3'))
        commands = ['ip route 1.1.1.0 /24 3.2.2.3 bfd']
        self.execute_module(changed=True, commands=commands)

    def test_vrf_bfd_iproute_no_change(self):
        set_module_args(dict(iproute_network_prefix='1.1.1.0',
                             iproute_mask_length=24,
                             iproute_next_hop='3.2.2.2',
                             vrf='3'))
        self.execute_module(changed=False)

    def test_vrf_bfd_iproute_with_change(self):
        set_module_args(dict(iproute_network_prefix='1.1.1.0',
                             iproute_mask_length=24,
                             iproute_next_hop='3.2.2.3',
                             vrf='3'))
        commands = ['ip route vrf 3 1.1.1.0 /24 3.2.2.3 bfd']
        self.execute_module(changed=True, commands=commands)
