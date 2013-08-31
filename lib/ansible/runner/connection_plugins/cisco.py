# (c) 2013, Benno Joy <benno@ansibleworks.com>
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

import os
import subprocess
import shlex
import pipes
import pexpect
import random
import select
import fcntl
import pwd
import ansible.constants as C
from ansible.callbacks import vvv
from ansible import errors
from ansible import utils

class Connection(object):
    ''' ssh based connections '''

    def __init__(self, runner, host, port, user, password, private_key_file, *args, **kwargs):
        self.runner = runner
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.private_key_file = private_key_file

    def connect(self):
        ''' connect to the remote host '''

        vvv("ESTABLISH CONNECTION FOR USER: %s" % self.user, host=self.host)

        self.common_args = []
        extra_args = C.ANSIBLE_SSH_ARGS
        if extra_args is not None:
            self.common_args += shlex.split(extra_args)
        else:
            self.common_args += ["-o", "ControlMaster=auto",
                                 "-o", "ControlPersist=60s",
                                 "-o", "ControlPath=/tmp/ansible-ssh-%h-%p-%r"]

        if not C.HOST_KEY_CHECKING:
            self.common_args += ["-o", "StrictHostKeyChecking=no"]

        if self.port is not None:
            self.common_args += ["-o", "Port=%d" % (self.port)]
        if self.private_key_file is not None:
            self.common_args += ["-o", "IdentityFile="+os.path.expanduser(self.private_key_file)]
        elif self.runner.private_key_file is not None:
            self.common_args += ["-o", "IdentityFile="+os.path.expanduser(self.runner.private_key_file)]
        if self.password:
            self.common_args += ["-o", "GSSAPIAuthentication=no",
                                 "-o", "PubkeyAuthentication=no"]
        else:
            self.common_args += ["-o", "KbdInteractiveAuthentication=no",
                                 "-o", "PasswordAuthentication=no"]
        if self.user != pwd.getpwuid(os.geteuid())[0]:
            self.common_args += ["-o", "User="+self.user]
        self.common_args += ["-o", "ConnectTimeout=%d" % self.runner.timeout]

        return self

    def make_connection(self, tmp_path):
	prompts = [">", "#", "\$", "}", ':', pexpect.TIMEOUT]
        enable_pass = tmp_path['enable_pass']
        if tmp_path['transport'] == 'telnet':
            if self.port == None:
                self.port = 23
            client_cmd = ["telnet"] + [self.host] + [str(self.port)]
            vvv("CONNECTION COMMAND: %s" % ' '.join(client_cmd), host=self.host)
            client = pexpect.spawn(' '.join(client_cmd), env = {"TERM": "dumb"})
            client.expect(prompts)
            client.sendline(self.user)
            client.expect(prompts)
            client.sendline(self.password)
            client.expect(prompts)
            if client.before.find('%') != -1:
                return (1,"Invalid Password Specified")
        else:
            client_cmd = ["ssh", "-tt", "-q"] + self.common_args + [self.host]
            vvv("CONNECTION COMMAND: %s" % ' '.join(client_cmd), host=self.host)
            client = pexpect.spawn(' '.join(client_cmd), env = {"TERM": "dumb"})
            client.expect(prompts)
            client.sendline(self.password)
            client.expect(prompts)
            if client.before.find('Password') != -1:
                return (1, "Invalid Password Specified")
	if tmp_path['enable'] != None:
            client.sendline("enable")
	    client.expect(prompts)
            client.sendline(enable_pass)
	    client.expect(prompts)
	    if client.before.find('%') != -1:
	        return (1, "Invalid Enable Password Specified")
        return (0, client)
        
    def exec_command(self, cmd, tmp_path, sudo_user,sudoable=False, executable=None):
        ''' run a command on the remote host '''
	executable = None
        rc = 0
        lines = []
	prompts = [">", "#", "\$", "}", ':', pexpect.TIMEOUT]
        rc1, client = self.make_connection(tmp_path)
        if rc1 == 1:	
            return (1,'', client, client)
        cmds = cmd.split("\n")
        for i in cmds:
            client.sendline(i)
	    line = client.readline().replace('\r\n', '')
	    lines += line
	    if line.find('%') != -1:
	        rc = 1
	        return (rc, '', ''.join(lines), ''.join(lines))
        if tmp_path['commit'] != None:
            rc1, client = self.make_connection(tmp_path)
            if rc1 == 1:	
                return (1, '', client, client)
            client.sendline("copy run startup")
	    client.expect(prompts)
            client.sendline(tmp_path['commit'])
	    client.expect(prompts)
	    lines += client.before.replace('\r\n', '')
	    if client.before.find('%') != -1:
	        return (1, '', "Issue in copying startup config", "Issue in copying starup config")
            
	return (rc, '', ''.join(lines), ''.join(lines))

    def close(self):
        ''' not applicable since we're executing openssh binaries '''
        pass
