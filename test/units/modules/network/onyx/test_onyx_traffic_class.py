#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_traffic_class
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxTrafficClassModule(TestOnyxModule):

    module = onyx_traffic_class
    arp_suppression = True

    def setUp(self):
        super(TestOnyxTrafficClassModule, self).setUp()
        self.mock_get_congestion_control_config = patch.object(
            onyx_traffic_class.OnyxTrafficClassModule, "_show_interface_congestion_control")
        self.get_congestion_control_config = self.mock_get_congestion_control_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_dcb_config = patch.object(
            onyx_traffic_class.OnyxTrafficClassModule, "_show_interface_dcb_ets")
        self.get_dcb_config = self.mock_get_dcb_config.start()

    def tearDown(self):
        super(TestOnyxTrafficClassModule, self).tearDown()
        self.mock_get_congestion_control_config.stop()
        self.mock_load_config.stop()
        self.mock_get_dcb_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        interfaces_congestion_control_config_file = 'onyx_show_interface_congestion_control.cfg'
        interfaces_dcb_config_file = 'onyx_show_dcb_ets_interface.cfg'
        interfaces_congestion_control_data = load_fixture(interfaces_congestion_control_config_file)
        interfaces_dcb_config_data = load_fixture(interfaces_dcb_config_file)
        self.get_congestion_control_config.return_value = interfaces_congestion_control_data
        self.get_dcb_config.return_value = interfaces_dcb_config_data
        self.load_config.return_value = None

    def test_configure_congestion_control_disabled_with_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=1,
                             congestion_control=dict(control="ecn", threshold_mode="absolute",
                                                     min_threshold=500, max_threshold=1500)))
        commands = [
            "interface ethernet 1/1 traffic-class 1 congestion-control ecn minimum-absolute 500 maximum-absolute 1500"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_configure_congestion_control_disabled_with_no_change(self):
        set_module_args(dict(state="disabled", interfaces=["Eth1/1"], tc=0))

        self.execute_module(changed=False)

    def test_configure_congestion_control_with_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=2,
                             congestion_control=dict(control="ecn", threshold_mode="relative",
                                                     min_threshold=9, max_threshold=88)))
        commands = [
            "interface ethernet 1/1 traffic-class 2 congestion-control ecn minimum-relative 9 maximum-relative 88"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_configure_congestion_control_absolute_with_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=3,
                             congestion_control=dict(control="ecn", threshold_mode="absolute",
                                                     min_threshold=500, max_threshold=1500)))
        commands = [
            "interface ethernet 1/1 traffic-class 3 congestion-control ecn minimum-absolute 500 maximum-absolute 1500"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_configure_congestion_control_with_no_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=3,
                             congestion_control=dict(control="ecn", threshold_mode="absolute",
                                                     min_threshold=500, max_threshold=1550)))
        self.execute_module(changed=False)

    def test_configure_dcb_mode_with_no_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=3, dcb=dict(mode="strict")))
        self.execute_module(changed=False)

    def test_configure_dcb_strict_mode_with_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=1, dcb=dict(mode="strict")))
        commands = [
            "interface ethernet 1/1 traffic-class 1 dcb ets strict"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_configure_dcb_wrr_mode_with_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=0, dcb=dict(mode="wrr", weight=10)))
        commands = [
            "interface ethernet 1/1 traffic-class 0 dcb ets wrr 10"
        ]
        self.execute_module(changed=True, commands=commands)

    def test_configure_dcb_wrr_mode_with_no_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], tc=0, dcb=dict(mode="wrr", weight=12)))

        self.execute_module(changed=False)
