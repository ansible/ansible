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
Compat module for Python3.x's unittest.mock module
'''

# Python 2.7

# Note: Could use the pypi mock library on python3.x as well as python2.x.  It
# is the same as the python3 stdlib mock library

try:
    from unittest.mock import *
except ImportError:
    # Python 2
    try:
        from mock import *
    except ImportError:
        print('You need the mock library installed on python2.x to run tests')
