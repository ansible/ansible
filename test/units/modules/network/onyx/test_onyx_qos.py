#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_qos
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxQosModule(TestOnyxModule):

    module = onyx_qos

    def setUp(self):
        super(TestOnyxQosModule, self).setUp()
        self.mock_get_if_qos_config = patch.object(
            onyx_qos.OnyxQosModule, "_show_interface_qos")
        self.get_if_qos_config = self.mock_get_if_qos_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxQosModule, self).tearDown()
        self.mock_get_if_qos_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        qos_interface_ethernet_config_file = 'show_qos_interface_ethernet.cfg'
        qos_interface_ethernet_data = load_fixture(qos_interface_ethernet_config_file)
        self.get_if_qos_config.return_value = qos_interface_ethernet_data
        self.load_config.return_value = None

    def test_qos_interface_ethernet_no_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], trust="both", rewrite_pcp="enabled",
                             rewrite_dscp="disabled"))
        self.execute_module(changed=False)

    def test_qos_interface_ethernet_with_change(self):
        set_module_args(dict(interfaces=["Eth1/1"], trust="L2", rewrite_pcp="disabled",
                             rewrite_dscp="enabled"))
        commands = ["interface ethernet 1/1 no qos rewrite pcp",
                    "interface ethernet 1/1 qos trust L2",
                    "interface ethernet 1/1 qos rewrite dscp"
                    ]
        self.execute_module(changed=True, commands=commands)
