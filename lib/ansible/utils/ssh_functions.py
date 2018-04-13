# (c) 2016, James Tanner
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

import subprocess

from ansible.module_utils._text import to_bytes


_HAS_CONTROLPERSIST = {}


def check_for_controlpersist(ssh_executable):
    try:
        # If we've already checked this executable
        return _HAS_CONTROLPERSIST[ssh_executable]
    except KeyError:
        pass

    b_ssh_exec = to_bytes(ssh_executable, errors='surrogate_or_strict')
    has_cp = True
    try:
        cmd = subprocess.Popen([b_ssh_exec, '-o', 'ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (out, err) = cmd.communicate()
        if b"Bad configuration option" in err or b"Usage:" in err:
            has_cp = False
    except OSError:
        has_cp = False

    _HAS_CONTROLPERSIST[ssh_executable] = has_cp
    return has_cp
