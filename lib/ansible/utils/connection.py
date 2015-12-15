# (c) 2015, Ansible, Inc. <support@ansible.com>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import subprocess
import sys


__all__ = ['get_smart_connection_type']

def get_smart_connection_type(play_context):
    '''
    Uses the ssh command with the ControlPersist option while checking
    for an error to determine if we should use ssh or paramiko. Also
    may take other factors into account.
    '''

    conn_type = 'ssh'
    if sys.platform.startswith('darwin') and play_context.password:
        # due to a current bug in sshpass on OSX, which can trigger
        # a kernel panic even for non-privileged users, we revert to
        # paramiko on that OS when a SSH password is specified
        conn_type = "paramiko"
    else:
        # see if SSH can support ControlPersist if not use paramiko
        try:
            cmd = subprocess.Popen(['ssh','-o','ControlPersist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (out, err) = cmd.communicate()
            if "Bad configuration option" in err or "Usage:" in err:
                conn_type = "paramiko"
        except OSError:
            conn_type = "paramiko"

    return conn_type
