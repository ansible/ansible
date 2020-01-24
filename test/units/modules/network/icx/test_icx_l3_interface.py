# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.icx import icx_l3_interface
from units.modules.utils import set_module_args
from .icx_module import TestICXModule, load_fixture


class TestICXFactsModule(TestICXModule):

    module = icx_l3_interface

    def setUp(self):
        super(TestICXFactsModule, self).setUp()
        self.mock_exec_command = patch('ansible.modules.network.icx.icx_l3_interface.exec_command')
        self.exec_command = self.mock_exec_command.start()
        self.mock_get_config = patch('ansible.modules.network.icx.icx_l3_interface.get_config')
        self.get_config = self.mock_get_config.start()
        self.mock_load_config = patch('ansible.modules.network.icx.icx_l3_interface.load_config')
        self.load_config = self.mock_load_config.start()
        self.set_running_config()

    def tearDown(self):
        super(TestICXFactsModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_exec_command.stop()

    def load_fixtures(self, commands=None):
        compares = None

        def load_from_file(*args, **kwargs):
            module = args
            for arg in args:
                if arg.params['check_running_config'] is True:
                    return load_fixture('show_running-config_begin_interface').strip()
                else:
                    return ''

        def write_config(*args, **kwargs):
            return ""

        self.get_config.side_effect = load_from_file
        self.load_config.side_effect = write_config

    def test_icx_l3_interface_set_ipv4(self):
        set_module_args(dict(name="ethernet 1/1/1", ipv4="192.168.1.1/24"))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                "interface ethernet 1/1/1",
                "ip address 192.168.1.1 255.255.255.0",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                "interface ethernet 1/1/1",
                "ip address 192.168.1.1 255.255.255.0",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)

    def test_icx_l3_interface_set_ipv6(self):
        set_module_args(dict(name="ethernet 1/1/1", ipv6="2001:db8:85a3:0:0:0:0:1/64"))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                "interface ethernet 1/1/1",
                "ipv6 address 2001:db8:85a3:0:0:0:0:1/64",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                "interface ethernet 1/1/1",
                "ipv6 address 2001:db8:85a3:0:0:0:0:1/64",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)

    def test_icx_l3_interface_remove_ipv6(self):
        set_module_args(dict(name="ethernet 1/1/1", ipv6="2001:db8:85a3:0:0:0:0:0/64", ipv4="192.168.1.1/24", state="absent"))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                "interface ethernet 1/1/1",
                "no ip address 192.168.1.1 255.255.255.0",
                "no ipv6 address 2001:db8:85a3:0:0:0:0:0/64",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                "interface ethernet 1/1/1",
                'no ip address 192.168.1.1 255.255.255.0',
                "no ipv6 address 2001:db8:85a3:0:0:0:0:0/64",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)

    def test_icx_l3_interface_set_aggregate(self):
        set_module_args(dict(aggregate=[
            dict(name="ve 1", ipv6="2001:db8:85a3:0:0:0:0:0/64", ipv4="192.168.1.1/24")
        ]))
        if not self.ENV_ICX_USE_DIFF:
            commands = [
                "interface ve 1",
                "ipv6 address 2001:db8:85a3:0:0:0:0:0/64",
                "ip address 192.168.1.1 255.255.255.0",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)
        else:
            commands = [
                "interface ve 1",
                "ipv6 address 2001:db8:85a3:0:0:0:0:0/64",
                "ip address 192.168.1.1 255.255.255.0",
                "exit"
            ]
            self.execute_module(commands=commands, changed=True)
