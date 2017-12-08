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

from ansible.compat.tests.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule
jnpr_mock = MagicMock()

modules = {
    'jnpr': jnpr_mock,
    'jnpr.junos': jnpr_mock.junos,
    'jnpr.junos.utils': jnpr_mock.junos.utils,
    'jnpr.junos.utils.sw': jnpr_mock.junos.utils.sw,
    'jnpr.junos.exception': jnpr_mock.junos.execption
}
module_patcher = patch.dict('sys.modules', modules)
module_patcher.start()

from ansible.modules.network.junos import junos_package


class TestJunosCommandModule(TestJunosModule):

    module = junos_package

    def setUp(self):
        super(TestJunosCommandModule, self).setUp()

    def tearDown(self):
        super(TestJunosCommandModule, self).tearDown()

    def test_junos_package_src(self):
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz'))
        result = self.execute_module(changed=True)
        args, kwargs = jnpr_mock.junos.utils.sw.SW().install.call_args
        self.assertEqual(args[0], 'junos-vsrx-12.1X46-D10.2-domestic.tgz')
        self.assertEqual(result['changed'], True)

    def test_junos_package_src_fail(self):
        jnpr_mock.junos.utils.sw.SW().install.return_value = 0
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz'))
        result = self.execute_module(changed=True, failed=True)
        self.assertEqual(result['msg'], 'Unable to install package on device')

    def test_junos_package_src_no_copy(self):
        jnpr_mock.junos.utils.sw.SW().install.return_value = 1
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz', no_copy=True))
        result = self.execute_module(changed=True)
        args, kwargs = jnpr_mock.junos.utils.sw.SW().install.call_args
        self.assertEqual(kwargs['no_copy'], True)

    def test_junos_package_device_param(self):
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz',
                             provider={'username': 'unit', 'host': 'test', 'ssh_keyfile': 'path',
                                       'password': 'test', 'port': 234}))
        self.execute_module(changed=True)
        args, kwargs = jnpr_mock.junos.Device.call_args

        self.assertEqual(args[0], 'test')
        self.assertEqual(kwargs['passwd'], 'test')
        self.assertEqual(kwargs['ssh_private_key_file'], 'path')
        self.assertEqual(kwargs['port'], 234)
        self.assertEqual(kwargs['user'], 'unit')
