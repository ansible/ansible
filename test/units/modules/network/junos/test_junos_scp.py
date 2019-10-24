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
modules = {
    'jnpr': jnpr_mock,
    'jnpr.junos': jnpr_mock.junos,
    'jnpr.junos.utils': jnpr_mock.junos.utils,
    'jnpr.junos.utils.scp': jnpr_mock.junos.utils.scp,
}
module_patcher = patch.dict('sys.modules', modules)
module_patcher.start()

from ansible.modules.network.junos import junos_scp


class TestJunosScpModule(TestJunosModule):

    module = junos_scp

    def setUp(self):
        super(TestJunosScpModule, self).setUp()
        self.mock_get_device = patch('ansible.modules.network.junos.junos_scp.get_device')
        self.get_device = self.mock_get_device.start()

        self.mock_scp = patch('ansible.modules.network.junos.junos_scp.SCP')
        self.scp = self.mock_scp.start()

        self.scp_mock = MagicMock()
        self.scp().__enter__.return_value = self.scp_mock

    def tearDown(self):
        super(TestJunosScpModule, self).tearDown()
        self.mock_get_device.stop()
        self.mock_scp.stop()

    def test_junos_scp_src(self):
        set_module_args(dict(src='test.txt'))
        self.execute_module(changed=True)

        self.scp_mock.put.assert_called_once_with('test.txt', remote_path='.', recursive=False)

    def test_junos_scp_src_fail(self):
        self.scp_mock.put.side_effect = OSError("[Errno 2] No such file or directory: 'text.txt'")
        set_module_args(dict(src='test.txt'))
        result = self.execute_module(changed=True, failed=True)

        self.assertEqual(result['msg'], "[Errno 2] No such file or directory: 'text.txt'")

    def test_junos_scp_remote_src(self):
        set_module_args(dict(src='test.txt', remote_src=True))
        self.execute_module(changed=True)

        self.scp_mock.get.assert_called_once_with('test.txt', local_path='.', recursive=False)

    def test_junos_scp_all(self):
        set_module_args(dict(src='test', remote_src=True, dest="tmp", recursive=True))
        self.execute_module(changed=True)

        self.scp_mock.get.assert_called_once_with('test', local_path='tmp', recursive=True)
