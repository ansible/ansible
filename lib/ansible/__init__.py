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

from sys import version_info as _python_version_tuple
_IS_PY2 = _python_version_tuple[0] == 2

# make vendored top-level modules accessible EARLY
if _IS_PY2:
    import ansible._vendor
else:
    from . import _vendor

# Note: Do not add any code to this file.  The ansible module may be
# a namespace package when using Ansible-2.1+ Anything in this file may not be
# available if one of the other packages in the namespace is loaded first.
#
# This is for backwards compat.  Code should be ported to get these from
# ansible.release instead of from here.
if _IS_PY2:
    from ansible.release import __version__, __author__
else:
    from .release import __version__, __author__
