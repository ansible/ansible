#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_wjh
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxWJHModule(TestOnyxModule):

    module = onyx_wjh

    def setUp(self):
        self.enabled = False
        super(TestOnyxWJHModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_wjh.OnyxWJHModule, "_get_wjh_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxWJHModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_wjh_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_wjh_no_change(self):
        set_module_args(dict(group='forwarding', enabled=False))
        self.execute_module(changed=False)

    def test_wjh_enable(self):
        set_module_args(dict(group='forwarding', enabled=True))
        commands = ['what-just-happened forwarding enable']
        self.execute_module(changed=True, commands=commands)

    def test_wjh_export_no_change(self):
        set_module_args(dict(export_group='forwarding', auto_export=False))
        self.execute_module(changed=False)

    def test_wjh_export_enable(self):
        set_module_args(dict(export_group='forwarding', auto_export=True))
        commands = ['what-just-happened auto-export forwarding enable']
        self.execute_module(changed=True, commands=commands)

    def test_wjh_export_disable(self):
        set_module_args(dict(export_group='all', auto_export=False))
        commands = ['no what-just-happened auto-export all enable']
        self.execute_module(changed=True, commands=commands)

    def test_wjh_clear(self):
        set_module_args(dict(clear_group='all'))
        commands = ['clear what-just-happened pcap-files all']
        self.execute_module(changed=True, commands=commands)
