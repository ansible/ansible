#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_syslog
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxSyslogModule(TestOnyxModule):

    module = onyx_syslog

    def setUp(self):
        self.enabled = False
        super(TestOnyxSyslogModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_syslog.OnyxSyslogModule, "_get_syslog_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxSyslogModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_syslog_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def test_syslog_local_level(self):
        set_module_args(dict(local_level='emerg'))
        commands = ['logging local emerg']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_trap(self):
        set_module_args(dict(trap='notice'))
        commands = ['logging trap notice']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_trap_disable(self):
        set_module_args(dict(trap_enabled='disabled'))
        commands = ['no logging trap']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_cli_level(self):
        set_module_args(dict(cli_level='alert'))
        commands = ['logging level cli commands alert']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_audit_level(self):
        set_module_args(dict(audit_level='notice'))
        commands = ['logging level audit mgmt notice']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_second_enable(self):
        set_module_args(dict(seconds_enabled='disabled'))
        commands = ['no logging fields seconds enabled']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_fractional_digits(self):
        set_module_args(dict(fractional_digits=2))
        commands = ['logging fields seconds fractional-digits 2']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_whole_digits(self):
        set_module_args(dict(whole_digits='6'))
        commands = ['logging fields seconds whole-digits 6']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_format(self):
        set_module_args(dict(format='welf', format_welf_host='test'))
        commands = ['logging format welf fw-name test']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_received(self):
        set_module_args(dict(received='yes'))
        commands = ['logging receive']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_monitor(self):
        set_module_args(dict(monitor=[dict(monitor_facility='mgmt-front', monitor_level='notice')]))
        commands = ['logging monitor mgmt-front notice']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_override(self):
        set_module_args(dict(local_override=[dict(override_class='mgmt-front', override_priority='notice')]))
        commands = ['logging local override class mgmt-front priority notice']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_override_disabled(self):
        set_module_args(dict(local_override=[dict(override_class='mgmt-front')], enabled="disabled"))
        commands = ['no logging local override class mgmt-front']
        self.execute_module(changed=True, commands=commands)

    def test_syslog_monitor_disabled(self):
        set_module_args(dict(monitor=[dict(monitor_facility='mgmt-front')], enabled="disabled"))
        commands = ['no logging monitor mgmt-front']
        self.execute_module(changed=True, commands=commands)

    '''no change'''
    def test_syslog_second_disable_no_change(self):
        set_module_args(dict(seconds_enabled='enabled'))
        self.execute_module(changed=False)

    def test_syslog_fractional_digits_no_change(self):
        set_module_args(dict(fractional_digits=6))
        self.execute_module(changed=False)

    def test_syslog_whole_digits_no_change(self):
        set_module_args(dict(whole_digits='all'))
        self.execute_module(changed=False)

    def test_syslog_received_no_changr(self):
        set_module_args(dict(received='no'))
        self.execute_module(changed=False)

    def test_syslog_monitor_no_changr(self):
        set_module_args(dict(monitor=[dict(monitor_facility='mgmt-front', monitor_level='emerg')]))
        self.execute_module(changed=False)

    def test_syslog_override_no_change(self):
        set_module_args(dict(local_override=[dict(override_class='debug-module', override_priority='notice')]))
        self.execute_module(changed=False)

    def test_syslog_monitor_disabled_no_change(self):
        set_module_args(dict(monitor=[dict(monitor_facility='mgmt-back')], enabled="disabled"))
        self.execute_module(changed=False)

    def test_syslog_override_disabled_no_change(self):
        set_module_args(dict(local_override=[dict(override_class='mgmt-back')], enabled="disabled"))
        self.execute_module(changed=False)
