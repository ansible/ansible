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
from ansible.modules.network.nxos import nxos_bfd_global
from ansible.module_utils.network.nxos.nxos import NxosCmdRef
from .nxos_module import TestNxosModule, load_fixture, set_module_args

# TBD: These imports / import checks are only needed as a workaround for
# shippable, which fails this test due to import yaml & import ordereddict.
import pytest
from ansible.module_utils.network.nxos.nxos import nxosCmdRef_import_check
msg = nxosCmdRef_import_check()
@pytest.mark.skipif(len(msg), reason=msg)
class TestNxosBfdGlobalModule(TestNxosModule):

    module = nxos_bfd_global

    def setUp(self):
        super(TestNxosBfdGlobalModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_bfd_global.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_execute_show_command = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.execute_show_command')
        self.execute_show_command = self.mock_execute_show_command.start()

        self.mock_get_platform_shortname = patch('ansible.module_utils.network.nxos.nxos.NxosCmdRef.get_platform_shortname')
        self.get_platform_shortname = self.mock_get_platform_shortname.start()

    def tearDown(self):
        super(TestNxosBfdGlobalModule, self).tearDown()
        self.mock_load_config.stop()
        self.execute_show_command.stop()
        self.get_platform_shortname.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None

    def test_bfd_defaults_n9k(self):
        # feature bfd is enabled, no non-defaults are set.
        self.execute_show_command.return_value = "feature bfd"
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            echo_interface='deleted',
            echo_rx_interval=50,
            interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            slow_timer=2000,
            startup_timer=5,
            ipv4_echo_rx_interval=50,
            ipv4_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            ipv4_slow_timer=2000,
            ipv6_echo_rx_interval=50,
            ipv6_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            ipv6_slow_timer=2000
        ))
        self.execute_module(changed=False)

    def test_bfd_non_defaults_n9k(self):
        # feature bfd is enabled, apply all non-default values.
        # This testcase also tests reordering of echo_interface to make sure
        # it gets applied last.
        self.execute_show_command.return_value = "feature bfd"
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            echo_interface='loopback1',
            echo_rx_interval=51,
            interval={'tx': 51, 'min_rx': 51, 'multiplier': 4},
            slow_timer=2001,
            startup_timer=6,
            ipv4_echo_rx_interval=51,
            ipv4_interval={'tx': 51, 'min_rx': 51, 'multiplier': 4},
            ipv4_slow_timer=2001,
            ipv6_echo_rx_interval=51,
            ipv6_interval={'tx': 51, 'min_rx': 51, 'multiplier': 4},
            ipv6_slow_timer=2001
        ))
        self.execute_module(changed=True, commands=[
            'bfd interval 51 min_rx 51 multiplier 4',
            'bfd ipv4 echo-rx-interval 51',
            'bfd ipv4 interval 51 min_rx 51 multiplier 4',
            'bfd ipv4 slow-timer 2001',
            'bfd ipv6 echo-rx-interval 51',
            'bfd ipv6 interval 51 min_rx 51 multiplier 4',
            'bfd ipv6 slow-timer 2001',
            'bfd slow-timer 2001',
            'bfd startup-timer 6',
            'bfd echo-interface loopback1',
            'bfd echo-rx-interval 51'
        ])

    def test_bfd_defaults_n3k(self):
        # feature bfd is enabled, no non-defaults are set.
        self.execute_show_command.return_value = "feature bfd"
        self.get_platform_shortname.return_value = 'N3K'
        set_module_args(dict(
            echo_interface='deleted',
            echo_rx_interval=250,
            interval={'tx': 250, 'min_rx': 250, 'multiplier': 3},
            slow_timer=2000,
            startup_timer=5,
            ipv4_echo_rx_interval=250,
            ipv4_interval={'tx': 250, 'min_rx': 250, 'multiplier': 3},
            ipv4_slow_timer=2000,
            ipv6_echo_rx_interval=250,
            ipv6_interval={'tx': 250, 'min_rx': 250, 'multiplier': 3},
            ipv6_slow_timer=2000
        ))
        self.execute_module(changed=False)

    def test_bfd_defaults_n35(self):
        # feature bfd is enabled, no non-defaults are set.
        self.execute_show_command.return_value = "feature bfd"
        self.get_platform_shortname.return_value = 'N35'
        set_module_args(dict(
            echo_interface='deleted',
            echo_rx_interval=50,
            interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            slow_timer=2000,
            startup_timer=5,
            ipv4_echo_rx_interval=50,
            ipv4_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            ipv4_slow_timer=2000,
        ))
        self.execute_module(changed=False)

    def test_bfd_defaults_n6k(self):
        # feature bfd is enabled, no non-defaults are set.
        self.execute_show_command.return_value = "feature bfd"
        self.get_platform_shortname.return_value = 'N6K'
        set_module_args(dict(
            echo_interface='deleted',
            interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            slow_timer=2000,
            fabricpath_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            fabricpath_slow_timer=2000,
            fabricpath_vlan=1
        ))
        self.execute_module(changed=False)

    def test_bfd_defaults_n7k(self):
        # feature bfd is enabled, no non-defaults are set.
        self.execute_show_command.return_value = "feature bfd"
        self.get_platform_shortname.return_value = 'N7K'
        set_module_args(dict(
            echo_interface='deleted',
            echo_rx_interval=50,
            interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            slow_timer=2000,
            ipv4_echo_rx_interval=50,
            ipv4_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            ipv4_slow_timer=2000,
            ipv6_echo_rx_interval=50,
            ipv6_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            ipv6_slow_timer=2000,
            fabricpath_interval={'tx': 50, 'min_rx': 50, 'multiplier': 3},
            fabricpath_slow_timer=2000,
            fabricpath_vlan=1
        ))
        self.execute_module(changed=False)

    def test_bfd_existing_n9k(self):
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.execute_show_command.return_value = load_fixture(module_name, 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            echo_interface='deleted',
            echo_rx_interval=51,
            interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            slow_timer=2000,
            startup_timer=5,
            ipv4_echo_rx_interval=50,
            ipv4_interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            ipv4_slow_timer=2000,
            ipv6_echo_rx_interval=50,
            ipv6_interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            ipv6_slow_timer=2000
        ))
        self.execute_module(changed=True, commands=[
            'no bfd echo-interface loopback2',
            'bfd echo-rx-interval 51',
            'bfd interval 51 min_rx 51 multiplier 3',
            'bfd slow-timer 2000',
            'bfd startup-timer 5',
            'bfd ipv4 echo-rx-interval 50',
            'bfd ipv4 interval 51 min_rx 51 multiplier 3',
            'bfd ipv4 slow-timer 2000',
            'bfd ipv6 echo-rx-interval 50',
            'bfd ipv6 interval 51 min_rx 51 multiplier 3',
            'bfd ipv6 slow-timer 2000',
        ])

    def test_bfd_idempotence_n9k(self):
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.execute_show_command.return_value = load_fixture(module_name, 'N9K.cfg')
        self.get_platform_shortname.return_value = 'N9K'
        set_module_args(dict(
            echo_interface='loopback2',
            echo_rx_interval=56,
            interval={'tx': 51, 'min_rx': 52, 'multiplier': 4},
            slow_timer=2001,
            startup_timer=6,
            ipv4_echo_rx_interval=54,
            ipv4_interval={'tx': 54, 'min_rx': 54, 'multiplier': 4},
            ipv4_slow_timer=2004,
            ipv6_echo_rx_interval=56,
            ipv6_interval={'tx': 56, 'min_rx': 56, 'multiplier': 6},
            ipv6_slow_timer=2006
        ))
        self.execute_module(changed=False)

    def test_bfd_existing_n7k(self):
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.execute_show_command.return_value = load_fixture(module_name, 'N7K.cfg')
        self.get_platform_shortname.return_value = 'N7K'
        set_module_args(dict(
            echo_interface='deleted',
            echo_rx_interval=51,
            interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            slow_timer=2002,
            ipv4_echo_rx_interval=51,
            ipv4_interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            ipv4_slow_timer=2002,
            ipv6_echo_rx_interval=51,
            ipv6_interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            ipv6_slow_timer=2002,
            fabricpath_interval={'tx': 51, 'min_rx': 51, 'multiplier': 3},
            fabricpath_slow_timer=2003,
            fabricpath_vlan=3,
        ))
        self.execute_module(changed=True, commands=[
            'no bfd echo-interface loopback2',
            'bfd echo-rx-interval 51',
            'bfd interval 51 min_rx 51 multiplier 3',
            'bfd slow-timer 2002',
            'bfd ipv4 echo-rx-interval 51',
            'bfd ipv4 interval 51 min_rx 51 multiplier 3',
            'bfd ipv4 slow-timer 2002',
            'bfd ipv6 echo-rx-interval 51',
            'bfd ipv6 interval 51 min_rx 51 multiplier 3',
            'bfd ipv6 slow-timer 2002',
            'bfd fabricpath interval 51 min_rx 51 multiplier 3',
            'bfd fabricpath slow-timer 2003',
            'bfd fabricpath vlan 3',
        ])

    def test_bfd_idempotence_n7k(self):
        module_name = self.module.__name__.rsplit('.', 1)[1]
        self.execute_show_command.return_value = load_fixture(module_name, 'N7K.cfg')
        self.get_platform_shortname.return_value = 'N7K'
        set_module_args(dict(
            echo_interface='loopback2',
            echo_rx_interval=56,
            interval={'tx': 51, 'min_rx': 52, 'multiplier': 4},
            slow_timer=2001,
            ipv4_echo_rx_interval=54,
            ipv4_interval={'tx': 54, 'min_rx': 54, 'multiplier': 4},
            ipv4_slow_timer=2004,
            ipv6_echo_rx_interval=56,
            ipv6_interval={'tx': 56, 'min_rx': 56, 'multiplier': 6},
            ipv6_slow_timer=2006,
            fabricpath_interval={'tx': 58, 'min_rx': 58, 'multiplier': 8},
            fabricpath_slow_timer=2008,
            fabricpath_vlan=2,
        ))
        self.execute_module(changed=False)
