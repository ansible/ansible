#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_syslog_files
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxSyslogFilesModule(TestOnyxModule):

    module = onyx_syslog_files

    def setUp(self):
        self.enabled = False
        super(TestOnyxSyslogFilesModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_syslog_files.OnyxSyslogFilesModule, "show_logging")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxSyslogFilesModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_logging_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_syslog_files_force_rotate(self):
        set_module_args(dict(rotation=dict(force=True)))
        commands = ["logging files rotation force"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_files_max_num(self):
        set_module_args(dict(rotation=dict(max_num=30)))
        commands = ["logging files rotation max-num 30"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_files_freq(self):
        set_module_args(dict(rotation=dict(frequency="daily")))
        commands = ["logging files rotation criteria frequency daily"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_files_size(self):
        set_module_args(dict(rotation=dict(size=10.5)))
        commands = ["logging files rotation criteria size 10.5"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_files_delete(self):
        set_module_args(dict(delete_group="oldest"))
        commands = ["logging files delete oldest"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_debug_files_force_rotate(self):
        set_module_args(dict(rotation=dict(force=True), debug=True))
        commands = ["logging debug-files rotation force"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_debug_files_max_num(self):
        set_module_args(dict(rotation=dict(max_num=30), debug=True))
        commands = ["logging debug-files rotation max-num 30"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_debug_files_freq(self):
        set_module_args(dict(rotation=dict(frequency="weekly"), debug=True))
        commands = ["logging debug-files rotation criteria frequency weekly"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_debug_files_size(self):
        set_module_args(dict(rotation=dict(size=10.5), debug=True))
        commands = ["logging debug-files rotation criteria size 10.5"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_debug_files_delete(self):
        set_module_args(dict(delete_group="oldest", debug=True))
        commands = ["logging debug-files delete oldest"]
        self.execute_module(changed=True, commands=commands)

    ''' nochange '''
    def test_syslog_files_max_num_no_change(self):
        set_module_args(dict(rotation=dict(max_num=10)))
        self.execute_module(changed=False)

    def test_syslog_files_freq_no_change(self):
        set_module_args(dict(rotation=dict(frequency="weekly")))
        self.execute_module(changed=False)

    def test_syslog_files_size_no_change(self):
        set_module_args(dict(rotation=dict(size_pct=10)))
        self.execute_module(changed=False)

    def test_syslog_debug_files_max_num_no_change(self):
        set_module_args(dict(rotation=dict(max_num=20), debug=True))
        self.execute_module(changed=False)

    def test_syslog_debug_files_freq_no_change(self):
        set_module_args(dict(rotation=dict(frequency="daily"), debug=True))
        self.execute_module(changed=False)

    def test_syslog_debug_files_size_no_change(self):
        set_module_args(dict(rotation=dict(size=20), debug=True))
        self.execute_module(changed=False)
