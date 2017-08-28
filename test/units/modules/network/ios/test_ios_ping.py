#
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

from ansible.modules.network.ios import ios_ping
from .ios_module import TestIosModule, load_fixture, set_module_args

class TestIosPingModule(TestIosModule):
    module = ios_ping

    def test_ios_ping_expected_success(self):
        set_module_args(dict(dest="8.8.8.8"))
        self.execute_module()

    def test_ios_ping_expected_failure(self):
        set_module_args(dict(dest="10.255.255.250", timeout=45))
        self.execute_module()

    def test_ios_ping_unexpected_success(self):
        set_module_args(dict(dest="8.8.8.8"))
        self.execute_module(failed=True)

    def test_ios_ping_unexpected_failure(self):
        set_module_args(dict(dest="10.255.255.250", timeout=45))
        self.execute_module(failed=True)
