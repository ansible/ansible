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

from ansible import errors
# prevent paramiko warning noise
# see http://stackoverflow.com/questions/3920502/
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


################################################

class ParamikoConnection(object):
    ''' SSH based connections with Paramiko '''

    def __init__(self, runner, host, port=None):
        self.ssh = None
        self.runner = runner
        self.host = host
        self.port = port
        if port is None:
            self.port = self.runner.remote_port

    def _get_conn(self):
        credentials = {}
        user = self.runner.remote_user
        keypair = None

        # Read file ~/.ssh/config, get data hostname, keyfile, port, etc
        # This will *NOT* overrides the ansible username and hostname " , getting the port and keyfile only.
	
        try:
            ssh_config = paramiko.SSHConfig()
            config_file = ('~/.ssh/config')
            if  os.path.exists(os.path.expanduser(config_file)):
                ssh_config.parse(open(os.path.expanduser(config_file)))
                credentials = ssh_config.lookup(self.host)

        except IOError,e:
                raise errors.AnsibleConnectionFailed(str(e))

        if 'port' in credentials:
            self.port = int(credentials['port'])
        if 'identityfile' in credentials:
            keypair = os.path.expanduser(credentials['identityfile'])

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                self.host,
                username=user,
                allow_agent=True,
                look_for_keys=True,
                password=self.runner.remote_pass,
                key_filename=keypair,
                timeout=self.runner.timeout,
                port=self.port
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

    def exec_command(self, cmd, tmp_path=None, sudo_user=None, sudoable=False):

        ''' run a command on the remote host '''
        bufsize = 4096
        chan = self.ssh.get_transport().open_session()
        chan.get_pty() 

        if not self.runner.sudo or not sudoable:
            quoted_command = '"$SHELL" -c ' + pipes.quote(cmd) 
            chan.exec_command(quoted_command)
        else:
            # Rather than detect if sudo wants a password this time, -k makes 
            # sudo always ask for a password if one is required. The "--"
            # tells sudo that this is the end of sudo options and the command
            # follows.  Passing a quoted compound command to sudo (or sudo -s)
            # directly doesn't work, so we shellquote it with pipes.quote() 
            # and pass the quoted string to the user's shell.  We loop reading
            # output until we see the randomly-generated sudo prompt set with
            # the -p option.
            randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
            prompt = '[sudo via ansible, key=%s] password: ' % randbits
            sudocmd = 'sudo -k -p "%s" -u %s -- "$SHELL" -c %s' % (prompt,
                    sudo_user, pipes.quote(cmd))
            sudo_output = ''
            try:
                chan.exec_command(sudocmd)
                if self.runner.sudo_pass:
                    while not sudo_output.endswith(prompt):
                        chunk = chan.recv(bufsize)
                        if not chunk:
                            raise errors.AnsibleError('ssh connection closed waiting for sudo password prompt')
                        sudo_output += chunk
                    chan.sendall(self.runner.sudo_pass + '\n')
            except socket.timeout:
                raise errors.AnsibleError('ssh timed out waiting for sudo.\n' + sudo_output)

        stdin = chan.makefile('wb', bufsize)
        stdout = chan.makefile('rb', bufsize)
        stderr = chan.makefile_stderr('rb', bufsize)        # stderr goes to stdout when using a pty, so this will never output anything.
        return stdin, stdout, stderr

    def put_file(self, in_path, out_path, mode=None):
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

        if mode:
            cmd = "chmod %s %s" % (mode, out_path)
            self.exec_command("chmod %s %s" % (mode, out_path))

    def fetch_file(self, in_path, out_path):
        sftp = self.ssh.open_sftp()
        try:
            sftp.get(in_path, out_path)
        except IOError:
            traceback.print_exc()
            raise errors.AnsibleError("failed to transfer file from %s" % in_path)
        sftp.close()

    def close(self):
        ''' terminate the connection '''

        self.ssh.close()

