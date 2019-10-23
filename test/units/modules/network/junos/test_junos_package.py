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

from units.compat.mock import patch, MagicMock
from units.modules.utils import set_module_args
from .junos_module import TestJunosModule

jnpr_mock = MagicMock()
modules = {
    'jnpr': jnpr_mock,
    'jnpr.junos': jnpr_mock.junos,
    'jnpr.junos.utils': jnpr_mock.junos.utils,
    'jnpr.junos.utils.sw': jnpr_mock.junos.utils.sw,
}
module_patcher = patch.dict('sys.modules', modules)
module_patcher.start()

from ansible.modules.network.junos import junos_package


class TestJunosPackageModule(TestJunosModule):

    module = junos_package

    def setUp(self):
        super(TestJunosPackageModule, self).setUp()
        self.mock_get_device = patch('ansible.modules.network.junos.junos_package.get_device')
        self.get_device = self.mock_get_device.start()

    def tearDown(self):
        super(TestJunosPackageModule, self).tearDown()
        self.mock_get_device.stop()

    def test_junos_package_src(self):
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz'))
        self.execute_module(changed=True)

        args, _kwargs = jnpr_mock.junos.utils.sw.SW().install.call_args
        self.assertEqual(args, ('junos-vsrx-12.1X46-D10.2-domestic.tgz',))

    def test_junos_package_src_fail(self):
        jnpr_mock.junos.utils.sw.SW().install.return_value = 0
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz'))
        result = self.execute_module(changed=True, failed=True)

        self.assertEqual(result['msg'], 'Unable to install package on device')

    def test_junos_package_src_no_copy(self):
        jnpr_mock.junos.utils.sw.SW().install.return_value = 1
        set_module_args(dict(src='junos-vsrx-12.1X46-D10.2-domestic.tgz', no_copy=True))
        self.execute_module(changed=True)

        args, kwargs = jnpr_mock.junos.utils.sw.SW().install.call_args
        self.assertEqual(args, ('junos-vsrx-12.1X46-D10.2-domestic.tgz',))
        self.assertEqual(kwargs['no_copy'], True)
