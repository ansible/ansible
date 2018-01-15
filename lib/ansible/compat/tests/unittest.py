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
Compat module for Python2.7's unittest module
'''

import sys

# Allow wildcard import because we really do want to import all of
# unittests's symbols into this compat shim
# pylint: disable=wildcard-import
if sys.version_info < (2, 7):
    try:
        # Need unittest2 on python2.6
        from unittest2 import *
    except ImportError:
        print('You need unittest2 installed on python2.6.x to run tests')
else:
    from unittest import *
