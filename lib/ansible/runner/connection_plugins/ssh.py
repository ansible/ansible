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
import ansible.constants as C
from ansible.callbacks import vvv
from ansible import errors

class Connection(object):
    ''' ssh based connections '''

    def __init__(self, runner, host, port):
        self.runner = runner
        self.host = host
        self.port = port

    def connect(self):
        ''' connect to the remote host '''

        vvv("ESTABLISH CONNECTION FOR USER: %s" % self.runner.remote_user, host=self.host)

        self.common_args = []
        extra_args = C.ANSIBLE_SSH_ARGS
        if extra_args is not None:
            self.common_args += shlex.split(extra_args)
        else:
            self.common_args += ["-o", "ControlMaster=auto",
                                 "-o", "ControlPersist=60s",
                                 "-o", "ControlPath=/tmp/ansible-ssh-%h-%p-%r"]
        self.common_args += ["-o", "StrictHostKeyChecking=no"]
        if self.port is not None:
            self.common_args += ["-o", "Port=%d" % (self.port)]
        if self.runner.private_key_file is not None:
            self.common_args += ["-o", "IdentityFile="+self.runner.private_key_file]
        if self.runner.remote_pass:
            self.common_args += ["-o", "GSSAPIAuthentication=no",
                                 "-o", "PubkeyAuthentication=no"]
        else:
            self.common_args += ["-o", "KbdInteractiveAuthentication=no",
                                 "-o", "PasswordAuthentication=no"]
        self.common_args += ["-o", "User="+self.runner.remote_user]

        return self

    def _password_cmd(self):
        if self.runner.remote_pass:
            try:
                p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
            except OSError:
                raise errors.AnsibleError("to use -c ssh with passwords, you must install the sshpass program")
            (self.rfd, self.wfd) = os.pipe()
            return ["sshpass", "-d%d" % self.rfd]
        return []

    def _send_password(self):
        if self.runner.remote_pass:
            os.close(self.rfd)
            os.write(self.wfd, "%s\n" % self.runner.remote_pass)
            os.close(self.wfd)

    def exec_command(self, cmd, tmp_path, sudo_user,sudoable=False):
        ''' run a command on the remote host '''

        ssh_cmd = self._password_cmd()
        ssh_cmd += ["ssh", "-tt", "-q"] + self.common_args + [self.host]

        if self.runner.sudo and sudoable:
            # Rather than detect if sudo wants a password this time, -k makes
            # sudo always ask for a password if one is required.
            # Passing a quoted compound command to sudo (or sudo -s)
            # directly doesn't work, so we shellquote it with pipes.quote()
            # and pass the quoted string to the user's shell.  We loop reading
            # output until we see the randomly-generated sudo prompt set with
            # the -p option.
            randbits = ''.join(chr(random.randint(ord('a'), ord('z'))) for x in xrange(32))
            prompt = '[sudo via ansible, key=%s] password: ' % randbits
            sudocmd = 'sudo -k && sudo -p "%s" -u %s /bin/sh -c %s' % (
                prompt, sudo_user, pipes.quote(cmd))
            cmd = sudocmd
        ssh_cmd.append('/bin/sh -c ' + pipes.quote(cmd))

        vvv("EXEC %s" % ssh_cmd, host=self.host)
        try:
            # Make sure stdin is a proper (pseudo) pty to avoid: tcgetattr errors
            import pty
            master, slave = pty.openpty()
            p = subprocess.Popen(ssh_cmd, stdin=slave,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdin = os.fdopen(master, 'w', 0)
        except:
            p = subprocess.Popen(ssh_cmd, stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdin = p.stdin

        self._send_password()

        if self.runner.sudo and sudoable and self.runner.sudo_pass:
            fcntl.fcntl(p.stdout, fcntl.F_SETFL,
                        fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            sudo_output = ''
            while not sudo_output.endswith(prompt):
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
            stdin.write(self.runner.sudo_pass + '\n')
            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        # We can't use p.communicate here because the ControlMaster may have stdout open as well
        stdout = ''
        while True:
            rfd, wfd, efd = select.select([p.stdout], [], [p.stdout], 1)
            if p.stdout in rfd:
                dat = os.read(p.stdout.fileno(), 9000)
                stdout += dat
                if dat == '':
                    p.wait()
                    break
            elif p.poll() is not None:
                break
        stdin.close() # close stdin after we read from stdout (see also issue #848)

        if p.returncode != 0 and stdout.find('Bad configuration option: ControlPersist') != -1:
            raise errors.AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" (or ansible_ssh_args in the config file) before running again')

        return ('', stdout, '')

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)
        cmd = self._password_cmd()

        if C.DEFAULT_SCP_IF_SSH:
            cmd += ["scp"] + self.common_args
            cmd += [in_path,self.host + ":" + out_path]
            indata = None
        else:
            cmd += ["sftp"] + self.common_args + [self.host]
            indata = "put %s %s\n" % (in_path, out_path)

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

        if C.DEFAULT_SCP_IF_SSH:
            cmd += ["scp"] + self.common_args
            cmd += [self.host + ":" + in_path, out_path]
            indata = None
        else:
            cmd += ["sftp"] + self.common_args + [self.host]
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

