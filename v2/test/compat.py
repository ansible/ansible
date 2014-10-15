# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import sys
import unittest

#
# Compat for python2.6
#

if sys.version_info < (2, 7):
    try:
        # Need unittest2 on python2.6
        import unittest2 as unittest
    except ImportError:
        print('You need unittest2 installed on python2.x')
else:
    import unittest


#
# Compat for python2.7
#

# Could use the pypi mock library on py3 as well as py2.  They are the same
try:
    from unittest.mock import mock_open, patch
except ImportError:
    # Python2
    from mock import mock_open, patch

try:
    import __builtin__
except ImportError:
    BUILTINS = 'builtins'
else:
    BUILTINS = '__builtin__'

