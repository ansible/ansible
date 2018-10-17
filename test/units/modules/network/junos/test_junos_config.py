#
# (c) 2017 Red Hat Inc.
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

from ansible.compat.tests.mock import patch
from ansible.modules.network.junos import junos_config
from units.modules.utils import set_module_args
from ansible.module_utils._text import to_text
from .junos_module import TestJunosModule, load_fixture


class TestJunosConfigModule(TestJunosModule):

    module = junos_config

    def setUp(self):
        super(TestJunosConfigModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.junos.junos_config.get_configuration')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.junos.junos_config.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_load_configuration = patch('ansible.modules.network.junos.junos_config.load_configuration')
        self.load_configuration = self.mock_load_configuration.start()

        self.mock_lock_configuration = patch('ansible.module_utils.network.junos.junos.lock_configuration')
        self.lock_configuration = self.mock_lock_configuration.start()

        self.mock_unlock_configuration = patch('ansible.module_utils.network.junos.junos.unlock_configuration')
        self.unlock_configuration = self.mock_unlock_configuration.start()

        self.mock_commit_configuration = patch('ansible.modules.network.junos.junos_config.commit_configuration')
        self.commit_configuration = self.mock_commit_configuration.start()

        self.mock_get_diff = patch('ansible.modules.network.junos.junos_config.get_diff')
        self.get_diff = self.mock_get_diff.start()

        self.mock_conn = patch('ansible.module_utils.connection.Connection')
        self.conn = self.mock_conn.start()

        self.mock_netconf = patch('ansible.module_utils.network.junos.junos.NetconfConnection')
        self.netconf_conn = self.mock_netconf.start()

        self.mock_exec_rpc = patch('ansible.modules.network.junos.junos_config.exec_rpc')
        self.exec_rpc = self.mock_exec_rpc.start()

        self.mock_netconf_rpc = patch('ansible.module_utils.network.common.netconf.NetconfConnection')
        self.netconf_rpc = self.mock_netconf_rpc.start()

    def tearDown(self):
        super(TestJunosConfigModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_lock_configuration.stop()
        self.mock_unlock_configuration.stop()
        self.mock_commit_configuration.stop()
        self.mock_get_diff.stop()
        self.load_configuration.stop()
        self.mock_conn.stop()
        self.mock_netconf.stop()
        self.mock_exec_rpc.stop()
        self.mock_netconf_rpc.stop()

    def load_fixtures(self, commands=None, format='text', changed=False):
        self.get_config.return_value = load_fixture('get_configuration_rpc_reply.txt')
        if changed:
            self.load_config.return_value = load_fixture('get_configuration_rpc_reply_diff.txt')
        else:
            self.load_config.return_value = None

    def test_junos_config_unchanged(self):
        src = load_fixture('junos_config.set', content='str')
        set_module_args(dict(src=src))
        self.execute_module()

    def test_junos_config_src_set(self):
        src = load_fixture('junos_config.set', content='str')
        set_module_args(dict(src=src))
        self.execute_module(changed=True)
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['action'], 'set')
        self.assertEqual(kwargs['format'], 'text')

    def test_junos_config_backup(self):
        set_module_args(dict(backup=True))
        result = self.execute_module()
        self.assertIn('__backup__', result)

    def test_junos_config_lines(self):
        set_module_args(dict(lines=['delete interfaces ae11', 'set interfaces ae11 unit 0 description Test']))
        self.execute_module(changed=True)
        args, kwargs = self.load_config.call_args
        self.assertEqual(args[1][0], 'set interfaces ae11 unit 0 description Test')
        self.assertEqual(kwargs['action'], 'set')
        self.assertEqual(kwargs['format'], 'text')

    def test_junos_config_confirm(self):
        src = load_fixture('junos_config.set', content='str')
        set_module_args(dict(src=src, confirm=40))
        self.execute_module(changed=True)
        args, kwargs = self.commit_configuration.call_args
        self.assertEqual(kwargs['confirm_timeout'], to_text(40))

    def test_junos_config_rollback(self):
        rollback = 10
        set_module_args(dict(rollback=rollback))
        self.execute_module(changed=True)
        self.assertEqual(self.get_diff.call_count, 1)
        self.assertEqual(self.load_configuration.call_count, 1)
        self.assertEqual(self.commit_configuration.call_count, 1)
        load_configuration_args = self.load_configuration.call_args
        self.assertEqual(rollback, load_configuration_args[1].get('rollback'))

    def test_junos_config_src_text(self):
        src = load_fixture('junos_config.text', content='str')
        set_module_args(dict(src=src))
        self.execute_module(changed=True)
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['action'], 'merge')
        self.assertEqual(kwargs['format'], 'text')

    def test_junos_config_src_xml(self):
        src = load_fixture('junos_config.xml', content='str')
        set_module_args(dict(src=src))
        self.execute_module(changed=True)
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['action'], 'merge')
        self.assertEqual(kwargs['format'], 'xml')

    def test_junos_config_src_json(self):
        src = load_fixture('junos_config.json', content='str')
        set_module_args(dict(src=src))
        self.execute_module(changed=True)
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['action'], 'merge')
        self.assertEqual(kwargs['format'], 'json')

    def test_junos_config_update_override(self):
        src = load_fixture('junos_config.xml', content='str')
        set_module_args(dict(src=src, update='override'))
        self.execute_module()
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['action'], 'override')
        self.assertEqual(kwargs['format'], 'xml')

    def test_junos_config_update_replace(self):
        src = load_fixture('junos_config.json', content='str')
        set_module_args(dict(src=src, update='replace'))
        self.execute_module()
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['action'], 'replace')
        self.assertEqual(kwargs['format'], 'json')

    def test_junos_config_zeroize(self):
        src = load_fixture('junos_config.json', content='str')
        set_module_args(dict(zeroize='yes'))
        self.execute_module(changed=True)
        self.assertEqual(self.exec_rpc.call_count, 1)

    def test_junos_config_src_format_xml(self):
        src = load_fixture('junos_config.json', content='str')
        set_module_args(dict(src=src, src_format='xml'))
        self.execute_module()
        args, kwargs = self.load_config.call_args
        self.assertEqual(kwargs['format'], 'xml')

    def test_junos_config_confirm_commit(self):
        set_module_args(dict(confirm_commit=True))
        self.execute_module(changed=True)
        self.assertEqual(self.commit_configuration.call_count, 1)
