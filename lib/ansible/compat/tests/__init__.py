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

'''
This module contains things that are only needed for compat in the testsuites,
not in ansible itself.  If you are not installing the test suite, you can
safely remove this subdirectory.
'''

#
# Compat for python2.7
#

# One unittest needs to import builtins via __import__() so we need to have
# the string that represents it
try:
    import __builtin__
except ImportError:
    BUILTINS = 'builtins'
else:
    BUILTINS = '__builtin__'
