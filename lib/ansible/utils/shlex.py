# (c) 2015, Marius Gedminas <marius@gedmin.as>
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
# alongwith Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import shlex
from ansible.compat.six import PY3

from ansible.utils.unicode import to_bytes, to_unicode


if PY3:
    # shlex.split() wants Unicode (i.e. ``str``) input on Python 3
    shlex_split = shlex.split
else:
    # shlex.split() wants bytes (i.e. ``str``) input on Python 2
    def shlex_split(s, comments=False, posix=True):
        return map(to_unicode, shlex.split(to_bytes(s), comments, posix))
    shlex_split.__doc__ = shlex.split.__doc__
