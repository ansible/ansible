# (c) 2018 Red Hat Inc.
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

from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule
jnpr_mock = MagicMock()
scp_mock = MagicMock()

modules = {
    'jnpr': jnpr_mock,
    'jnpr.junos': jnpr_mock.junos,
    'jnpr.junos.utils': jnpr_mock.junos.utils,
    'jnpr.junos.utils.scp': jnpr_mock.junos.utils.scp,
    'jnpr.junos.exception': jnpr_mock.junos.execption
}
module_patcher = patch.dict('sys.modules', modules)
module_patcher.start()

jnpr_mock.junos.utils.scp.SCP().__enter__.return_value = scp_mock

from ansible.modules.network.junos import junos_scp


class TestJunosCommandModule(TestJunosModule):

    module = junos_scp

    def setUp(self):
        super(TestJunosCommandModule, self).setUp()

    def tearDown(self):
        super(TestJunosCommandModule, self).tearDown()

    def test_junos_scp_src(self):
        set_module_args(dict(src='test.txt'))
        result = self.execute_module(changed=True)
        args, kwargs = scp_mock.put.call_args
        self.assertEqual(args[0], 'test.txt')
        self.assertEqual(result['changed'], True)

    def test_junos_scp_src_fail(self):
        scp_mock.put.side_effect = OSError("[Errno 2] No such file or directory: 'text.txt'")
        set_module_args(dict(src='test.txt'))
        result = self.execute_module(changed=True, failed=True)
        self.assertEqual(result['msg'], "[Errno 2] No such file or directory: 'text.txt'")

    def test_junos_scp_remote_src(self):
        set_module_args(dict(src='test.txt', remote_src=True))
        result = self.execute_module(changed=True)
        args, kwargs = scp_mock.get.call_args
        self.assertEqual(args[0], 'test.txt')
        self.assertEqual(result['changed'], True)

    def test_junos_scp_all(self):
        set_module_args(dict(src='test', remote_src=True, dest="tmp", recursive=True))
        result = self.execute_module(changed=True)
        args, kwargs = scp_mock.get.call_args
        self.assertEqual(args[0], 'test')
        self.assertEqual(kwargs['local_path'], 'tmp')
        self.assertEqual(kwargs['recursive'], True)
        self.assertEqual(result['changed'], True)

    def test_junos_scp_device_param(self):
        set_module_args(dict(src='test.txt',
                             provider={'username': 'unit', 'host': 'test', 'ssh_keyfile': 'path',
                                       'password': 'test', 'port': 234}))
        self.execute_module(changed=True)
        args, kwargs = jnpr_mock.junos.Device.call_args

        self.assertEqual(args[0], 'test')
        self.assertEqual(kwargs['passwd'], 'test')
        self.assertEqual(kwargs['ssh_private_key_file'], 'path')
        self.assertEqual(kwargs['port'], 234)
        self.assertEqual(kwargs['user'], 'unit')
