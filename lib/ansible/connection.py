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

import paramiko
import traceback
import os
import time
from ansible import errors

################################################

class Connection(object):
    ''' Handles abstract connections to remote hosts '''

    def __init__(self, runner, transport):
        self.runner = runner
        self.transport = transport

    def connect(self, host):
        conn = None
        if self.transport == 'paramiko':
            conn = ParamikoConnection(self.runner, host)
        if conn is None:
            raise Exception("unsupported connection type")
        return conn.connect()

################################################
# want to implement another connection type?
# follow duck-typing of ParamikoConnection
# you may wish to read config files in __init__
# if you have any.  Paramiko does not need any.

class ParamikoConnection(object):
    ''' SSH based connections with Paramiko '''

    def __init__(self, runner, host):
        self.ssh = None
        self.runner = runner
        self.host = host

    def _get_conn(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                self.host, username=self.runner.remote_user,
                allow_agent=True, look_for_keys=True, password=self.runner.remote_pass,
                timeout=self.runner.timeout, port=self.runner.remote_port
            )
        except Exception, e:
            if str(e).find("PID check failed") != -1:
                raise errors.AnsibleError("paramiko version issue, please upgrade paramiko on the machine running ansible")
            else:
                raise errors.AnsibleConnectionFailed(str(e))

        return ssh


    def connect(self):
        ''' connect to the remote host '''

        self.ssh = self._get_conn()
        return self

    def exec_command(self, cmd, sudoable=True):

        ''' run a command on the remote host '''
        if not self.runner.sudo or not sudoable: 
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            return (stdin, stdout, stderr)
        else:
            # this code is a work in progress, so it's disabled...
            self.ssh.close()
            ssh_sudo = self._get_conn()
            sudo_chan = ssh_sudo.invoke_shell()
            sudo_chan.send("sudo -s\n")
            sudo_chan.recv(1024)
            sudo_chan.send("echo && %s && echo\n" % cmd)
            while not sudo_chan.recv_ready():
                # TODO: timeout support
                time.sleep(1)
            out = sudo_chan.recv(1024)
            sudo_chan.close()
            self.ssh = self._get_conn()
            out = self._expect_like(out)
            return (None, out, '')

    def _expect_like(self, msg):
        ''' hack to make invoke_shell more or less work for sudo usage '''
        lines = msg.split("\n")
        index = 0
        for x in lines:
            if x == '\r':
                break
            index += 1
        index2 = index+1 
        for x in lines[index:]:
            if x == '\r':
                break
            index2 += 1
        return "\n".join(lines[index+1:index2+1]).strip()

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        sftp = self.ssh.open_sftp()
        try:
            sftp.put(in_path, out_path)
        except IOError:
            traceback.print_exc()
            raise errors.AnsibleError("failed to transfer file to %s" % out_path)
        sftp.close()

    def close(self):
        ''' terminate the connection '''

        self.ssh.close()

############################################
# add other connection types here


