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
import exceptions
    
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

class AnsibleConnectionException(exceptions.Exception):
    ''' Subclass of exception for catching in Runner() code '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

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

    def connect(self):
        ''' connect to the remote host '''

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(
                self.host, 
                username=self.runner.remote_user, 
                allow_agent=True,
                look_for_keys=True, 
                password=self.runner.remote_pass, 
                timeout=self.runner.timeout
            )
        except Exception, e:
            raise AnsibleConnectionException(str(e))
        return self

    def exec_command(self, cmd):
        ''' run a command on the remote host '''

        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        return (stdin, stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        sftp = self.ssh.open_sftp()
        sftp.put(in_path, out_path)
        sftp.close()

    def close(self):
        ''' terminate the connection '''

        self.ssh.close()

############################################
# add other connection types here


