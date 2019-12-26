#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_bgp_peer_groups
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxBgpPeerGroupsModule(TestOnyxModule):

    module = onyx_bgp_peer_groups

    def setUp(self):
        super(TestOnyxBgpPeerGroupsModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_bgp_peer_groups.OnyxBgpPeerGroupsModule, "_show_bgp_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxBgpPeerGroupsModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_show_bgp_peer_groups.cfg'
        data = load_fixture(config_file)
        self.get_config.return_value = data
        self.load_config.return_value = None
