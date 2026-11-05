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

# The __future__ import statement has been intentionally omitted here
# to increase the range of Python versions which can execute the version check below.

import os as _os
import sys as _sys

_MIN_PYTHON_VERSION = (3, 13)
_MAX_PYTHON_VERSION = (3, 15)
_SYS_PYTHON_VERSION = _sys.version_info[:2]

if _SYS_PYTHON_VERSION < _MIN_PYTHON_VERSION or _SYS_PYTHON_VERSION > _MAX_PYTHON_VERSION:
    _BYPASS_KEY = 'ANSIBLE_ALLOW_UNSUPPORTED_PYTHON'

    if not _os.environ.get(_BYPASS_KEY):
        _min_python_str = '.'.join(map(str, _MIN_PYTHON_VERSION))
        _max_python_str = '.'.join(map(str, _MAX_PYTHON_VERSION))
        _sys_python_str = '.'.join(map(str, _SYS_PYTHON_VERSION))

        raise SystemExit(
            "ERROR: "
            f"Ansible requires Python {_min_python_str} - {_max_python_str} on the controller, "
            f"but {_sys_python_str} is currently in use. "
            f"Set the {_BYPASS_KEY!r} environment variable to bypass this check at your own risk."
        )

# make vendored top-level modules accessible EARLY
import ansible._vendor

# This is for backwards compat.  Code should be ported to get these from
# ansible.release instead of from here.
from ansible.release import __version__, __author__
