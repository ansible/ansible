# (c) 2016 Red Hat Inc.
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

import pytest

pytestmark = []
try:
    from ansible.modules.network.fortimanager import fmgr_provisioning
    from .fortimanager_module import TestFortimanagerModule
    from units.modules.utils import set_module_args
except ImportError:
    pytestmark.append(pytest.mark.skip("Could not load required modules for testing"))

try:
    from pyFMG.fortimgr import FortiManager
except ImportError:
    pytestmark.append(pytest.mark.skip("FortiManager tests require pyFMG package"))


class TestFmgrProvisioningModule(TestFortimanagerModule):

    module = fmgr_provisioning

    def test_fmg_script_fail_connect(self):
        set_module_args(dict(host='1.1.1.1', username='admin', password='admin', adom='root',
                             vdom='root', policy_package='root', name='FGT1', serial='FGVM000000117992',
                             platform='FortiGate-VM64', os_version='5.0', minor_release='6',
                             patch_release='0', os_type='fos'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Connection to FortiManager Failed')

    def test_fmg_script_login_fail_host(self):
        set_module_args(dict(username='admin', password='admin', adom='root',
                             vdom='root', policy_package='root', name='FGT1', serial='FGVM000000117992',
                             platform='FortiGate-VM64', os_version='5.0', minor_release='6',
                             patch_release='0', os_type='fos'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'missing required arguments: host')

    def test_fmg_script_login_fail_username(self):
        set_module_args(dict(host='1.1.1.1', password='admin', adom='root',
                             vdom='root', policy_package='root', name='FGT1', serial='FGVM000000117992',
                             platform='FortiGate-VM64', os_version='5.0', minor_release='6',
                             patch_release='0', os_type='fos'))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Host and username are required for connection')
