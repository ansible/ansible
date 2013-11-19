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

import os
import subprocess
import shlex
import pipes
import random
import select
import fcntl
import hmac
import pwd
import gettext
import pty
from hashlib import sha1
import ansible.constants as C
from ansible.callbacks import vvv
from ansible import errors
from ansible import utils

class Connection(object):
    ''' ssh based connections '''

    def __init__(self, runner, host, port, user, password, private_key_file, *args, **kwargs):
        self.runner = runner
        self.host = host
        self.ipv6 = ':' in self.host
        self.port = port
        self.user = user
        self.password = password
        self.private_key_file = private_key_file
        self.HASHED_KEY_MAGIC = "|1|"

        fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_EX)
        self.cp_dir = utils.prepare_writeable_dir('$HOME/.ansible/cp',mode=0700)
        fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_UN)

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
                                 "-o", "ControlPath=%s" % (C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self.cp_dir))]

        cp_in_use = False
        cp_path_set = False
        for arg in self.common_args:
            if arg.find("ControlPersist") != -1:
                cp_in_use = True
            if arg.find("ControlPath") != -1:
                cp_path_set = True

        if cp_in_use and not cp_path_set:
            self.common_args += ["-o", "ControlPath=%s" % (C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self.cp_dir))]

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
                                 "-o", "PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
                                 "-o", "PasswordAuthentication=no"]
        if self.user != pwd.getpwuid(os.geteuid())[0]:
            self.common_args += ["-o", "User="+self.user]
        self.common_args += ["-o", "ConnectTimeout=%d" % self.runner.timeout]

        return self

    def _password_cmd(self):
        if self.password:
            try:
                p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
            except OSError:
                raise errors.AnsibleError("to use the 'ssh' connection type with passwords, you must install the sshpass program")
            (self.rfd, self.wfd) = os.pipe()
            return ["sshpass", "-d%d" % self.rfd]
        return []

    def _send_password(self):
        if self.password:
            os.close(self.rfd)
            os.write(self.wfd, "%s\n" % self.password)
            os.close(self.wfd)

    def not_in_host_file(self, host):
        host_file = os.path.expanduser(os.path.expandvars("~${USER}/.ssh/known_hosts"))
        if not os.path.exists(host_file):
            print "previous known host file not found"
            return True
        host_fh = open(host_file)
        data = host_fh.read()
        host_fh.close()
        for line in data.split("\n"):
            if line is None or line.find(" ") == -1:
                continue
            tokens = line.split()
            if tokens[0].find(self.HASHED_KEY_MAGIC) == 0:
                # this is a hashed known host entry
                try:
                    (kn_salt,kn_host) = tokens[0][len(self.HASHED_KEY_MAGIC):].split("|",2)
                    hash = hmac.new(kn_salt.decode('base64'), digestmod=sha1)
                    hash.update(host)
                    if hash.digest() == kn_host.decode('base64'):
                        return False
                except:
                    # invalid hashed host key, skip it
                    continue
            else:
                # standard host file entry
                if host in tokens[0]:
                    return False
        return True

    def exec_command(self, cmd, tmp_path, sudo_user,sudoable=False, executable='/bin/sh'):
        ''' run a command on the remote host '''

        ssh_cmd = self._password_cmd()
        ssh_cmd += ["ssh", "-tt"]
        if utils.VERBOSITY > 3:
            ssh_cmd += ["-vvv"]
        else:
            ssh_cmd += ["-q"]
        ssh_cmd += self.common_args

        if self.ipv6:
            ssh_cmd += ['-6']
        ssh_cmd += [self.host]

        if not self.runner.sudo or not sudoable:
            if executable:
                ssh_cmd.append(executable + ' -c ' + pipes.quote(cmd))
            else:
                ssh_cmd.append(cmd)
        else:
            sudocmd, prompt, success_key = utils.make_sudo_cmd(sudo_user, executable, cmd)
            ssh_cmd.append(sudocmd)

        vvv("EXEC %s" % ssh_cmd, host=self.host)

        not_in_host_file = self.not_in_host_file(self.host)

        if C.HOST_KEY_CHECKING and not_in_host_file:
            # lock around the initial SSH connectivity so the user prompt about whether to add 
            # the host to known hosts is not intermingled with multiprocess output.
            fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_EX)
            fcntl.lockf(self.runner.output_lockfile, fcntl.LOCK_EX)
        


        try:
            # Make sure stdin is a proper (pseudo) pty to avoid: tcgetattr errors
            master, slave = pty.openpty()
            p = subprocess.Popen(ssh_cmd, stdin=slave,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdin = os.fdopen(master, 'w', 0)
            os.close(slave)
        except:
            p = subprocess.Popen(ssh_cmd, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdin = p.stdin

        self._send_password()

        if self.runner.sudo and sudoable and self.runner.sudo_pass:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL,
                        fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            sudo_output = ''
            while not sudo_output.endswith(prompt) and success_key not in sudo_output:
                rfd, wfd, efd = select.select([p.stdout], [],
                                              [p.stdout], self.runner.timeout)
                if p.stdout in rfd:
                    chunk = p.stdout.read()
                    if not chunk:
                        raise errors.AnsibleError('ssh connection closed waiting for sudo password prompt')
                    sudo_output += chunk
                else:
                    stdout = p.communicate()
                    raise errors.AnsibleError('ssh connection error waiting for sudo password prompt')
            if success_key not in sudo_output:
                stdin.write(self.runner.sudo_pass + '\n')
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        # We can't use p.communicate here because the ControlMaster may have stdout open as well
        stdout = ''
        stderr = ''
        rpipes = [p.stdout, p.stderr]
        while True:
            rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

            # fail early if the sudo password is wrong
            if self.runner.sudo and sudoable and self.runner.sudo_pass:
                incorrect_password = gettext.dgettext(
                    "sudo", "Sorry, try again.")
                if stdout.endswith("%s\r\n%s" % (incorrect_password, prompt)):
                    raise errors.AnsibleError('Incorrect sudo password') 

            if p.stdout in rfd:
                dat = os.read(p.stdout.fileno(), 9000)
                stdout += dat
                if dat == '':
                    rpipes.remove(p.stdout)
            if p.stderr in rfd:
                dat = os.read(p.stderr.fileno(), 9000)
                stderr += dat
                if dat == '':
                    rpipes.remove(p.stderr)
            if not rpipes or p.poll() is not None:
                p.wait()
                break
        stdin.close() # close stdin after we read from stdout (see also issue #848)
        
        if C.HOST_KEY_CHECKING and not_in_host_file:
            # lock around the initial SSH connectivity so the user prompt about whether to add 
            # the host to known hosts is not intermingled with multiprocess output.
            fcntl.lockf(self.runner.output_lockfile, fcntl.LOCK_UN)
            fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_UN)

        if p.returncode != 0 and stderr.find('Bad configuration option: ControlPersist') != -1:
            raise errors.AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" (or ansible_ssh_args in the config file) before running again')

        return (p.returncode, '', stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        cmd = self._password_cmd()

        host = self.host
        if self.ipv6:
            host = '[%s]' % host

        if C.DEFAULT_SCP_IF_SSH:
            cmd += ["scp"] + self.common_args
            cmd += [in_path,host + ":" + pipes.quote(out_path)]
            indata = None
        else:
            cmd += ["sftp"] + self.common_args + [host]
            indata = "put %s %s\n" % (pipes.quote(in_path), pipes.quote(out_path))

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._send_password()
        stdout, stderr = p.communicate(indata)

        if p.returncode != 0:
            raise errors.AnsibleError("failed to transfer file to %s:\n%s\n%s" % (out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        cmd = self._password_cmd()

        host = self.host
        if self.ipv6:
            host = '[%s]' % host

        if C.DEFAULT_SCP_IF_SSH:
            cmd += ["scp"] + self.common_args
            cmd += [host + ":" + in_path, out_path]
            indata = None
        else:
            cmd += ["sftp"] + self.common_args + [host]
            indata = "get %s %s\n" % (in_path, out_path)

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._send_password()
        stdout, stderr = p.communicate(indata)

        if p.returncode != 0:
            raise errors.AnsibleError("failed to transfer file from %s:\n%s\n%s" % (in_path, stdout, stderr))

    def close(self):
        ''' not applicable since we're executing openssh binaries '''
        pass

