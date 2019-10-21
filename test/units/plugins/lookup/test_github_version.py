# (c) 2019 Ari Kalfus <dev@quantummadness.com>
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

# TODO: Add the freaking tests
# Test 1: correct format (ansible/ansible)
# Test 2: correct format with symbols (test-name/whatever&happened*to#this@repo+name)
# Test 3: incorrect format: spaces in repo name (test-name/a repo)
# Test 4: incorrect format: symbols in orgname/username (not&allowed/repo)
# Test 5: incorrect format: empty string
# Test 6: incorrect format: missing repo name (empty list)
