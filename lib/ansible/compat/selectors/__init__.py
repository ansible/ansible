# (c) 2014, 2017 Toshio Kuratomi <tkuratomi@ansible.com>
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
Compat selectors library.  Python-3.5 has this builtin.  The selectors2
package exists on pypi to backport the functionality as far as python-2.6.
'''
# The following makes it easier for us to script updates of the bundled code
_BUNDLED_METADATA = {"pypi_name": "selectors2", "version": "1.1.0"}
# Added these bugfix commits from 2.1.0:
# * https://github.com/SethMichaelLarson/selectors2/commit/3bd74f2033363b606e1e849528ccaa76f5067590
#   Wrap kqueue.control so that timeout is a keyword arg
# * https://github.com/SethMichaelLarson/selectors2/commit/6f6a26f42086d8aab273b30be492beecb373646b
#   Fix formatting of the kqueue.control patch for pylint
# * https://github.com/SethMichaelLarson/selectors2/commit/f0c2c6c66cfa7662bc52beaf4e2d65adfa25e189
#   Fix use of OSError exception for py3 and use the wrapper of kqueue.control so retries of
#   interrupted syscalls work with kqueue

import os.path
import sys

try:
    # Python 3.4+
    import selectors as _system_selectors
except ImportError:
    try:
        # backport package installed in the system
        import selectors2 as _system_selectors
    except ImportError:
        _system_selectors = None

if _system_selectors:
    selectors = _system_selectors
else:
    # Our bundled copy
    from . import _selectors2 as selectors
sys.modules['ansible.compat.selectors'] = selectors
