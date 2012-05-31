# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
#

################################################

import warnings
import traceback
import os
import time
import re
import shutil
import subprocess
import pipes
import socket
import random

from ansible.runner.connection import local
from ansible.runner.connection import paramiko_ssh

class Connection(object):
    ''' Handles abstract connections to remote hosts '''

    def __init__(self, runner, transport,sudo_user):
        self.runner = runner
        self.transport = transport
        self.sudo_user = sudo_user
    def connect(self, host, port=None):
        conn = None
        if self.transport == 'local':
            conn = local.LocalConnection(self.runner, host)
        elif self.transport == 'paramiko':
            conn = paramiko_ssh.ParamikoConnection(self.runner, host, port)
        if conn is None:
            raise Exception("unsupported connection type")
        return conn.connect()

