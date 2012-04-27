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

from ansible import errors
# prevent paramiko warning noise
# see http://stackoverflow.com/questions/3920502/
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


################################################



class Connection(object):
    ''' Handles abstract connections to remote hosts '''

    _LOCALHOSTRE = re.compile(r"^(127.0.0.1|localhost|%s)$" % os.uname()[1])

    def __init__(self, runner, transport):
        self.runner = runner
        self.transport = transport

    def connect(self, host, port=None):
        conn = None
        if self.transport == 'local' and self._LOCALHOSTRE.search(host):
            conn = LocalConnection(self.runner, host)
        elif self.transport == 'paramiko':
            conn = ParamikoConnection(self.runner, host, port)
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

        #if 'hostname' in credentials:
        #    self.host = credentials['hostname']
        if 'port' in credentials:
            self.port = int(credentials['port'])
        #if 'user' in credentials:
        #    user = credentials['user']
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

    def exec_command(self, cmd, tmp_path, sudoable=False):          # pylint: disable-msg=W0613
        ''' run a command on the remote host '''
        bufsize = 4096                              # Could make this a Runner param if needed
        timeout_secs = self.runner.timeout          # Reusing runner's TCP connect timeout as command progress timeout
        chan = self.ssh.get_transport().open_session()
        chan.settimeout(timeout_secs)
        chan.get_pty()                              # Many sudo setups require a terminal; use in both cases for consistency
        
        if not self.runner.sudo or not sudoable:
            quoted_command = '"$SHELL" -c ' + pipes.quote(cmd) 
            chan.exec_command(quoted_command)
        else:
            # Rather than detect if sudo wants a password this time, -k makes 
            # sudo always ask for a password if one is required. The "--"
            # tells sudo that this is the end of sudo options and the command
            # follows.  Passing a quoted compound command to sudo (or sudo -s)
            # directly doesn't work, so we shellquote it with pipes.quote() 
            # and pass the quoted string to the user's shell.
            sudocmd = 'sudo -k -- "$SHELL" -c ' + pipes.quote(cmd) 
            chan.exec_command(sudocmd)
            if self.runner.sudo_pass:
                while not chan.recv_ready():
                    time.sleep(0.25)
                sudo_output = chan.recv(bufsize)        # Pull prompt, catch errors, eat sudo output
                chan.sendall(self.runner.sudo_pass + '\n')

        stdin = chan.makefile('wb', bufsize) 
        stdout = chan.makefile('rb', bufsize)
        stderr = chan.makefile_stderr('rb', bufsize) 
        return stdin, stdout, stderr

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

############################################
# add other connection types here

class LocalConnection(object):
    ''' Local based connections '''

    def __init__(self, runner, host):
        self.runner = runner
        self.host = host

    def connect(self, port=None):
        ''' connect to the local host; nothing to do here '''

        return self

    def exec_command(self, cmd, tmp_path, sudoable=False):
        ''' run a command on the local host '''
        if self.runner.sudo and sudoable:
            cmd = "sudo -s %s" % cmd
        if self.runner.sudo_pass:
            # NOTE: if someone wants to add sudo w/ password to the local connection type, they are welcome
            # to do so.  The primary usage of the local connection is for crontab and kickstart usage however
            # so this doesn't seem to be a huge priority
            raise errors.AnsibleError("sudo with password is presently only supported on the paramiko (SSH) connection type")

        p = subprocess.Popen(cmd, shell=True, stdin=None,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return ("", stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to local '''
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        try:
            shutil.copyfile(in_path, out_path)
        except shutil.Error:
            traceback.print_exc()
            raise errors.AnsibleError("failed to copy: %s and %s are the same" % (in_path, out_path))
        except IOError:
            traceback.print_exc()
            raise errors.AnsibleError("failed to transfer file to %s" % out_path)

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from local to local -- for copatibility '''
        self.put_file(in_path, out_path)

    def close(self):
        ''' terminate the connection; nothing to do here '''

        pass
