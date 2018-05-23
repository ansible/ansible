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

from nose.plugins.skip import SkipTest

try:
    from ansible.modules.network.fortimanager import fmgr_fwpol_ipv4
    from .fortimanager_module import TestFortimanagerModule
    from units.modules.utils import set_module_args
except ImportError:
    raise SkipTest("Could not load required modules for testing")

try:
    from pyFMG.fortimgr import FortiManager
except ImportError:
    raise SkipTest("FortiManager tests require pyFMG package")


class TestFmgrQueryModule(TestFortimanagerModule):

    module = fmgr_fwpol_ipv4

    def test_fmgr_fwpol_ipv4_fail_connect(self):
        set_module_args(dict(host='10.1.1.1', username='ansible', password='fortinet', package_name="ansible",
                             adom="ansible", name="testRule",
                             action="accept", dstaddr="all", srcaddr="all", dstintf="any", srcintf="any",
                             logtraffic="utm", service="ALL", schedule="always"))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Connection to FortiManager Failed')

    def test_fmgr_fwpol_ipv4_login_fail_host(self):
        set_module_args(dict(username='ansible', password='fortinet', action="accept", dstaddr="all",
                             package_name="ansible", adom="ansible", name="testRule",
                             srcaddr="all", dstintf="any", srcintf="any", logtraffic="utm",
                             service="ALL", schedule="always"))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'missing required arguments: host')

    def test_fmgr_fwpol_ipv4_login_fail_username(self):
        set_module_args(dict(host='10.1.1.1', password='fortinet', action="accept", dstaddr="all",
                             package_name="ansible", adom="ansible", name="testRule",
                             srcaddr="all", dstintf="any", srcintf="any", logtraffic="utm",
                             service="ALL", schedule="always"))
        result = self.execute_module(failed=True)
        self.assertEqual(result['msg'], 'Host and username are required')
