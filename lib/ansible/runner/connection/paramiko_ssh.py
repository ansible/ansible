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

import warnings
import traceback
import os
import re
import shutil
import subprocess
import pipes
import socket
import random
from ansible import errors

# prevent paramiko warning noise -- see http://stackoverflow.com/questions/3920502/
HAVE_PARAMIKO=False
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    try:
        import paramiko
        HAVE_PARAMIKO=True
    except ImportError:
        pass

class ParamikoConnection(object):
    ''' SSH based connections with Paramiko '''

    def __init__(self, runner, host, port=None):
        self.ssh = None
        self.runner = runner
        self.host = host
        self.port = port
        if port is None:
            self.port = self.runner.remote_port

    def connect(self):
        ''' activates the connection object '''

        if not HAVE_PARAMIKO:
            raise errors.AnsibleError("paramiko is not installed")

        user = self.runner.remote_user
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(self.host, username=user, allow_agent=True, look_for_keys=True,
                key_filename=self.runner.private_key_file, password=self.runner.remote_pass,
                timeout=self.runner.timeout, port=self.port)
        except Exception, e:
            msg = str(e)
            if "PID check failed" in msg:
                raise errors.AnsibleError("paramiko version issue, please upgrade paramiko on the machine running ansible")
            elif "Private key file is encrypted" in msg:
                msg = 'ssh %s@%s:%s : %s\nTo connect as a different user, use -u <username>.' % (
                    user, self.host, self.port, msg)
                raise errors.AnsibleConnectionFailed(msg)
            else:
                raise errors.AnsibleConnectionFailed(msg)

        self.ssh = ssh
        return self

    def exec_command(self, cmd, tmp_path, sudo_user, sudoable=False):
        ''' run a command on the remote host '''

        bufsize = 4096
        chan = self.ssh.get_transport().open_session()
        chan.get_pty() 

        quoted_command = '"$SHELL" -c ' + pipes.quote(cmd) 
        if not self.runner.sudo and not self.runner.su or not sudoable:
            chan.exec_command(quoted_command)
        else:
            if self.runner.sudo: 
                sudocmd = 'sudo -u %s -- %s' % (sudo_user, quoted_command)
            if self.runner.su:
                sudocmd = 'su %s -c %s' % (sudo_user, quoted_command)
            sudo_output = ''
            try:
                chan.exec_command(sudocmd)
                if self.runner.sudo_pass:
                    while not sudo_output.endswith('assword: '):
                        chunk = chan.recv(bufsize)
                        if not chunk:
                            raise errors.AnsibleError('ssh connection closed waiting for password prompt')
                        sudo_output += chunk
                    chan.sendall(self.runner.sudo_pass + '\n')
            except socket.timeout:
                raise errors.AnsibleError('ssh timed out waiting for sudo.\n' + sudo_output)

        return (chan.makefile('wb', bufsize), chan.makefile('rb', bufsize), '')

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        sftp = self.ssh.open_sftp()
        try:
            sftp.put(in_path, out_path)
        except IOError:
            raise errors.AnsibleError("failed to transfer file to %s" % out_path)
        sftp.close()

    def fetch_file(self, in_path, out_path):
        ''' save a remote file to the specified path '''
        sftp = self.ssh.open_sftp()
        try:
            sftp.get(in_path, out_path)
        except IOError:
            raise errors.AnsibleError("failed to transfer file from %s" % in_path)
        sftp.close()

    def close(self):
        ''' terminate the connection '''
        self.ssh.close()

