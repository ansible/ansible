# (c) 2014, Toshio Kuratomi <tkuratomi@ansible.com>
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

# Allow wildcard import because we really do want to import all of
# unittests's symbols into this compat shim
# pylint: disable=wildcard-import,unused-wildcard-import
from unittest import *

if not hasattr(TestCase, 'assertRaisesRegex'):
    # added in Python 3.2
    TestCase.assertRaisesRegex = TestCase.assertRaisesRegexp
