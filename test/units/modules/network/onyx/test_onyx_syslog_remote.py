#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_syslog_remote
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxSysLogRemoteModule(TestOnyxModule):

    module = onyx_syslog_remote

    def setUp(self):
        self.enabled = False
        super(TestOnyxSysLogRemoteModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_syslog_remote.OnyxSyslogRemoteModule, "show_logging")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxSysLogRemoteModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_logging_config_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_syslog_new_host(self):
        set_module_args(dict(host="10.10.20.20"))
        commands = ["logging 10.10.20.20"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_new_host_port(self):
        set_module_args(dict(host="10.10.20.20", port=8080))
        commands = ['logging 10.10.20.20', 'logging 10.10.20.20 port 8080']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_override(self):
        set_module_args(dict(host="10.10.10.12", trap_override=[dict(override_class="sx-sdk", override_priority='emerg'),
                                                                dict(override_class="mgmt-back", override_priority='emerg')]))
        commands = ["logging 10.10.10.12 trap override class mgmt-back priority emerg"]  # no sx-sdk its already configured
        self.execute_module(changed=True, commands=commands)

    def test_syslog_trap(self):
        set_module_args(dict(host="10.10.10.10", trap="notice"))
        commands = ["logging 10.10.10.10 trap notice"]
        self.execute_module(changed=True, commands=commands)

    def test_syslog_include_filter(self):
        set_module_args(dict(host="10.10.10.10", filter="include", filter_str=".*ERR.*"))
        commands = ['logging 10.10.10.10 filter include .*ERR.*']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_no_override(self):
        set_module_args(dict(host="10.10.10.12", trap_override=[dict(override_class="sx-sdk", override_enabled=False),
                                                                dict(override_class="mgmt-front", override_enabled=False)]))
        commands = ['no logging 10.10.10.12 trap override class sx-sdk']  # no mgmt-front because doesn't configured
        self.execute_module(changed=True, commands=commands)

    def test_syslog_no_port(self):
        set_module_args(dict(host="10.10.10.12", enabled=False))
        commands = ['no logging 10.10.10.12']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_filter_no_change(self):
        set_module_args(dict(host="10.10.10.10", filter="exclude", filter_str=".*ERR.*"))
        self.execute_module(changed=False)

    def test_syslog_trap_no_change(self):
        set_module_args(dict(host="10.10.10.10", trap="info"))
        self.execute_module(changed=False)

    def test_syslog_add_port_no_change(self):
        set_module_args(dict(host="10.10.10.12", port=80))
        self.execute_module(changed=False)

    def test_syslog_override_no_change(self):
        set_module_args(dict(host="10.10.10.12", trap_override=[dict(override_priority="emerg", override_class="sx-sdk")]))
        self.execute_module(changed=False)
