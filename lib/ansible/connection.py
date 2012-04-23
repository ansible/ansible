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
# prevent paramiko warning noise
# see http://stackoverflow.com/questions/3920502/
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko

import traceback
import os
import time
import random
import re
import shutil
import subprocess
from ansible import errors

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
            conn = LocalConnection(self.runner, host, None)
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
	credentials = None 
	user = self.runner.remote_user 
	keypair = None 

	# Read file ~/.ssh/config, get data hostname, keyfile, port, etc
	# This overrides the ansible defined username,hostname and port 
	try:
            ssh_config = paramiko.SSHConfig()
	    config_file = ('~/.ssh/config')
            ssh_config.parse(open(os.path.expanduser(config_file)))
  	    credentials = ssh_config.lookup(self.host) 
	    if 'hostname' in credentials: 
               self.host = credentials['hostname']	
	    if 'port' in credentials: 
               self.port = credentials['port']	
        except IOError,e:
                raise errors.AnsibleConnectionFailed(str(e))

	if 'user' in credentials: 
            user = credentials['user']	
	if 'identityfile' in credentials:
            keypair = credentials['identityfile']	

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

    def exec_command(self, cmd, tmp_path, sudoable=False):
        ''' run a command on the remote host '''
        if not self.runner.sudo or not sudoable: 
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            return (stdin, stdout, stderr)
        else:
            # percalculated tmp_path is ONLY required for sudo usage
            if tmp_path is None:
                raise Exception("expecting tmp_path")
            r = random.randint(0,99999)
            
            # invoke command using a new connection over sudo
            result_file = os.path.join(tmp_path, "sudo_result.%s" % r)
            self.ssh.close()
            ssh_sudo = self._get_conn()
            sudo_chan = ssh_sudo.invoke_shell()
            sudo_chan.send("sudo -s\n")

            # FIXME: using sudo with a password adds more delay, someone may wish
            # to optimize to see when the channel is actually ready
            if self.runner.sudo_pass:
                time.sleep(0.1) # this is conservative
                sudo_chan.send("%s\n" % self.runner.sudo_pass)
                time.sleep(0.1)

            # to avoid ssh expect logic, redirect output to file and move the
            # file when we are done with it...
            sudo_chan.send("(%s >%s_pre 2>/dev/null ; mv %s_pre %s) &\n" % (cmd, result_file, result_file, result_file))
            # FIXME: someone may wish to optimize to not background the launch, and tell when the command
            # returns, removing the time.sleep(1) here
            time.sleep(1)
            sudo_chan.close()
            self.ssh = self._get_conn()

            # now load the results of the JSON execution...
            # FIXME: really need some timeout logic here
            # though it doesn't make since to use the SSH timeout or impose any particular
            # limit.  Upgrades welcome.
            sftp = self.ssh.open_sftp()
            while True:
                # print "waiting on %s" % result_file
                time.sleep(1)
                try:
                    sftp.stat(result_file)
                    break
                except IOError:
                    pass
            sftp.close()
            # TODO: see if there's a SFTP way to just get the file contents w/o saving
            # to disk vs this hack...
            stdin, stdout, stderr = self.ssh.exec_command("cat %s" % result_file)
            return (stdin, stdout, stderr)

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

