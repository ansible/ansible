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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
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

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.plugins.connections import ConnectionBase

class Connection(ConnectionBase):
    ''' ssh based connections '''

    def __init__(self, *args, **kwargs):
        # SSH connection specific init stuff
        self.HASHED_KEY_MAGIC = "|1|"
        self._has_pipelining = True

        # FIXME: move the lockfile locations to ActionBase?
        #fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_EX)
        #self.cp_dir = utils.prepare_writeable_dir('$HOME/.ansible/cp',mode=0700)
        self._cp_dir = '/tmp'
        #fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_UN)

        super(Connection, self).__init__(*args, **kwargs)

    @property
    def transport(self):
        ''' used to identify this connection object from other classes '''
        return 'ssh'

    def _connect(self):
        ''' connect to the remote host '''

        self._display.vvv("ESTABLISH SSH CONNECTION FOR USER: {0}".format(self._connection_info.remote_user), host=self._connection_info.remote_addr)

        if self._connected:
            return self

        self._common_args = []
        extra_args = C.ANSIBLE_SSH_ARGS
        if extra_args is not None:
            # make sure there is no empty string added as this can produce weird errors
            self._common_args += [x.strip() for x in shlex.split(extra_args) if x.strip()]
        else:
            self._common_args += (
                "-o", "ControlMaster=auto",
                "-o", "ControlPersist=60s",
                "-o", "ControlPath=\"{0}\"".format(C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self._cp_dir)),
            )

        cp_in_use = False
        cp_path_set = False
        for arg in self._common_args:
            if "ControlPersist" in arg:
                cp_in_use = True
            if "ControlPath" in arg:
                cp_path_set = True

        if cp_in_use and not cp_path_set:
            self._common_args += ("-o", "ControlPath=\"{0}\"".format(
                C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self._cp_dir))
            )

        if not C.HOST_KEY_CHECKING:
            self._common_args += ("-o", "StrictHostKeyChecking=no")

        if self._connection_info.port is not None:
            self._common_args += ("-o", "Port={0}".format(self._connection_info.port))
        # FIXME: need to get this from connection info
        #if self.private_key_file is not None:
        #    self._common_args += ("-o", "IdentityFile=\"{0}\"".format(os.path.expanduser(self.private_key_file)))
        #elif self.runner.private_key_file is not None:
        #    self._common_args += ("-o", "IdentityFile=\"{0}\"".format(os.path.expanduser(self.runner.private_key_file)))
        if self._connection_info.password:
            self._common_args += ("-o", "GSSAPIAuthentication=no",
                                 "-o", "PubkeyAuthentication=no")
        else:
            self._common_args += ("-o", "KbdInteractiveAuthentication=no",
                                 "-o", "PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
                                 "-o", "PasswordAuthentication=no")
        if self._connection_info.remote_user is not None and self._connection_info.remote_user != pwd.getpwuid(os.geteuid())[0]:
            self._common_args += ("-o", "User={0}".format(self._connection_info.remote_user))
        # FIXME: figure out where this goes
        #self._common_args += ("-o", "ConnectTimeout={0}".format(self.runner.timeout))
        self._common_args += ("-o", "ConnectTimeout=15")

        self._connected = True

        return self

    def _run(self, cmd, indata):
        if indata:
            # do not use pseudo-pty
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdin = p.stdin
        else:
            # try to use upseudo-pty
            try:
                # Make sure stdin is a proper (pseudo) pty to avoid: tcgetattr errors
                master, slave = pty.openpty()
                p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = os.fdopen(master, 'w', 0)
                os.close(slave)
            except:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = p.stdin

        return (p, stdin)

    def _password_cmd(self):
        if self._connection_info.password:
            try:
                p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
            except OSError:
                raise AnsibleError("to use the 'ssh' connection type with passwords, you must install the sshpass program")
            (self.rfd, self.wfd) = os.pipe()
            return ("sshpass", "-d{0}".format(self.rfd))
        return []

    def _send_password(self):
        if self._connection_info.password:
            os.close(self.rfd)
            os.write(self.wfd, "{0}\n".format(self._connection_info.password))
            os.close(self.wfd)

    def _communicate(self, p, stdin, indata, su=False, sudoable=False, prompt=None):
        fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
        fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)
        # We can't use p.communicate here because the ControlMaster may have stdout open as well
        stdout = ''
        stderr = ''
        rpipes = [p.stdout, p.stderr]
        if indata:
            try:
                stdin.write(indata)
                stdin.close()
            except:
                raise AnsibleConnectionFailure('SSH Error: data could not be sent to the remote host. Make sure this host can be reached over ssh')
        # Read stdout/stderr from process
        while True:
            rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

            # FIXME: su/sudo stuff
            # fail early if the sudo/su password is wrong
            #if self.runner.sudo and sudoable:
            #    if self.runner.sudo_pass:
            #        incorrect_password = gettext.dgettext(
            #            "sudo", "Sorry, try again.")
            #        if stdout.endswith("%s\r\n%s" % (incorrect_password,
            #                                         prompt)):
            #            raise AnsibleError('Incorrect sudo password')
            #
            #    if stdout.endswith(prompt):
            #        raise AnsibleError('Missing sudo password')
            #
            #if self.runner.su and su and self.runner.su_pass:
            #    incorrect_password = gettext.dgettext(
            #        "su", "Sorry")
            #    if stdout.endswith("%s\r\n%s" % (incorrect_password, prompt)):
            #        raise AnsibleError('Incorrect su password')

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
            # only break out if no pipes are left to read or
            # the pipes are completely read and
            # the process is terminated
            if (not rpipes or not rfd) and p.poll() is not None:
                break
            # No pipes are left to read but process is not yet terminated
            # Only then it is safe to wait for the process to be finished
            # NOTE: Actually p.poll() is always None here if rpipes is empty
            elif not rpipes and p.poll() == None:
                p.wait()
                # The process is terminated. Since no pipes to read from are
                # left, there is no need to call select() again.
                break
        # close stdin after process is terminated and stdout/stderr are read
        # completely (see also issue #848)
        stdin.close()
        return (p.returncode, stdout, stderr)

    def not_in_host_file(self, host):
        if 'USER' in os.environ:
            user_host_file = os.path.expandvars("~${USER}/.ssh/known_hosts")
        else:
            user_host_file = "~/.ssh/known_hosts"
        user_host_file = os.path.expanduser(user_host_file)

        host_file_list = []
        host_file_list.append(user_host_file)
        host_file_list.append("/etc/ssh/ssh_known_hosts")
        host_file_list.append("/etc/ssh/ssh_known_hosts2")

        hfiles_not_found = 0
        for hf in host_file_list:
            if not os.path.exists(hf):
                hfiles_not_found += 1
                continue
            try:
                host_fh = open(hf)
            except IOError as e:
                hfiles_not_found += 1
                continue
            else:
                data = host_fh.read()
                host_fh.close()

            for line in data.split("\n"):
                if line is None or " " not in line:
                    continue
                tokens = line.split()
                if not tokens:
                    continue
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

        if (hfiles_not_found == len(host_file_list)):
            self._display.vvv("EXEC previous known host file not found for {0}".format(host))
        return True

    def exec_command(self, cmd, tmp_path, executable='/bin/sh', in_data=None):
        ''' run a command on the remote host '''

        ssh_cmd = self._password_cmd()
        ssh_cmd += ("ssh", "-C")
        if not in_data:
            # we can only use tty when we are not pipelining the modules. piping data into /usr/bin/python
            # inside a tty automatically invokes the python interactive-mode but the modules are not
            # compatible with the interactive-mode ("unexpected indent" mainly because of empty lines)
            ssh_cmd.append("-tt")
        if self._connection_info.verbosity > 3:
            ssh_cmd.append("-vvv")
        else:
            ssh_cmd.append("-q")
        ssh_cmd += self._common_args

        # FIXME: ipv6 stuff needs to be figured out. It's in the connection info, however
        #        not sure if it's all working yet so this remains commented out
        #if self._ipv6:
        #    ssh_cmd += ['-6']
        ssh_cmd.append(self._connection_info.remote_addr)

        ssh_cmd.append(cmd)
        self._display.vvv("EXEC {0}".format(' '.join(ssh_cmd)), host=self._connection_info.remote_addr)

        not_in_host_file = self.not_in_host_file(self._connection_info.remote_addr)

        # FIXME: move the locations of these lock files, same as init above
        #if C.HOST_KEY_CHECKING and not_in_host_file:
        #    # lock around the initial SSH connectivity so the user prompt about whether to add 
        #    # the host to known hosts is not intermingled with multiprocess output.
        #    fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_EX)
        #    fcntl.lockf(self.runner.output_lockfile, fcntl.LOCK_EX)

        # create process
        (p, stdin) = self._run(ssh_cmd, in_data)

        self._send_password()

        no_prompt_out = ''
        no_prompt_err = ''
        # FIXME: su/sudo stuff
        #if (self.runner.sudo and sudoable and self.runner.sudo_pass) or \
        #        (self.runner.su and su and self.runner.su_pass):
        #    # several cases are handled for sudo privileges with password
        #    # * NOPASSWD (tty & no-tty): detect success_key on stdout
        #    # * without NOPASSWD:
        #    #   * detect prompt on stdout (tty)
        #    #   * detect prompt on stderr (no-tty)
        #    fcntl.fcntl(p.stdout, fcntl.F_SETFL,
        #                fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
        #    fcntl.fcntl(p.stderr, fcntl.F_SETFL,
        #                fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
        #    sudo_output = ''
        #    sudo_errput = ''
        #
        #    while True:
        #        if success_key in sudo_output or \
        #            (self.runner.sudo_pass and sudo_output.endswith(prompt)) or \
        #            (self.runner.su_pass and utils.su_prompts.check_su_prompt(sudo_output)):
        #            break
        #
        #        rfd, wfd, efd = select.select([p.stdout, p.stderr], [],
        #                                      [p.stdout], self.runner.timeout)
        #        if p.stderr in rfd:
        #            chunk = p.stderr.read()
        #            if not chunk:
        #                raise AnsibleError('ssh connection closed waiting for sudo or su password prompt')
        #            sudo_errput += chunk
        #            incorrect_password = gettext.dgettext(
        #                "sudo", "Sorry, try again.")
        #            if sudo_errput.strip().endswith("%s%s" % (prompt, incorrect_password)):
        #                raise AnsibleError('Incorrect sudo password')
        #            elif sudo_errput.endswith(prompt):
        #                stdin.write(self.runner.sudo_pass + '\n')
        #
        #        if p.stdout in rfd:
        #            chunk = p.stdout.read()
        #            if not chunk:
        #                raise AnsibleError('ssh connection closed waiting for sudo or su password prompt')
        #            sudo_output += chunk
        #
        #        if not rfd:
        #            # timeout. wrap up process communication
        #            stdout = p.communicate()
        #            raise AnsibleError('ssh connection error waiting for sudo or su password prompt')
        #
        #    if success_key not in sudo_output:
        #        if sudoable:
        #            stdin.write(self.runner.sudo_pass + '\n')
        #        elif su:
        #            stdin.write(self.runner.su_pass + '\n')
        #    else:
        #        no_prompt_out += sudo_output
        #        no_prompt_err += sudo_errput

        #(returncode, stdout, stderr) = self._communicate(p, stdin, in_data, su=su, sudoable=sudoable, prompt=prompt)
        # FIXME: the prompt won't be here anymore
        prompt=""
        (returncode, stdout, stderr) = self._communicate(p, stdin, in_data, prompt=prompt)

        #if C.HOST_KEY_CHECKING and not_in_host_file:
        #    # lock around the initial SSH connectivity so the user prompt about whether to add 
        #    # the host to known hosts is not intermingled with multiprocess output.
        #    fcntl.lockf(self.runner.output_lockfile, fcntl.LOCK_UN)
        #    fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_UN)
        controlpersisterror = 'Bad configuration option: ControlPersist' in stderr or 'unknown configuration option: ControlPersist' in stderr

        if C.HOST_KEY_CHECKING:
            if ssh_cmd[0] == "sshpass" and p.returncode == 6:
                raise AnsibleError('Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support this.  Please add this host\'s fingerprint to your known_hosts file to manage this host.')

        if p.returncode != 0 and controlpersisterror:
            raise AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" (or ssh_args in [ssh_connection] section of the config file) before running again')
        # FIXME: module name isn't in runner
        #if p.returncode == 255 and (in_data or self.runner.module_name == 'raw'):
        if p.returncode == 255 and in_data:
            raise AnsibleConnectionFailure('SSH Error: data could not be sent to the remote host. Make sure this host can be reached over ssh')

        return (p.returncode, '', no_prompt_out + stdout, no_prompt_err + stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''
        self._display.vvv("PUT {0} TO {1}".format(in_path, out_path), host=self._connection_info.remote_addr)
        if not os.path.exists(in_path):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(in_path))
        cmd = self._password_cmd()

        # FIXME: make a function, used in all 3 methods EXEC/PUT/FETCH
        host = self._connection_info.remote_addr

        # FIXME: ipv6 stuff needs to be figured out. It's in the connection info, however
        #        not sure if it's all working yet so this remains commented out
        #if self._ipv6:
        #    host = '[%s]' % host

        if C.DEFAULT_SCP_IF_SSH:
            cmd.append('scp')
            cmd += self._common_args
            cmd.append(in_path,host + ":" + pipes.quote(out_path))
            indata = None
        else:
            cmd.append('sftp')
            cmd += self._common_args
            cmd.append(host)
            indata = "put {0} {1}\n".format(pipes.quote(in_path), pipes.quote(out_path))

        (p, stdin) = self._run(cmd, indata)

        self._send_password()

        (returncode, stdout, stderr) = self._communicate(p, stdin, indata)

        if returncode != 0:
            raise AnsibleError("failed to transfer file to {0}:\n{1}\n{2}".format(out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''
        self._display.vvv("FETCH {0} TO {1}".format(in_path, out_path), host=self._connection_info.remote_addr)
        cmd = self._password_cmd()

        # FIXME: make a function, used in all 3 methods EXEC/PUT/FETCH
        host = self._connection_info.remote_addr

        # FIXME: ipv6 stuff needs to be figured out. It's in the connection info, however
        #        not sure if it's all working yet so this remains commented out
        #if self._ipv6:
        #    host = '[%s]' % self._connection_info.remote_addr

        if C.DEFAULT_SCP_IF_SSH:
            cmd.append('scp')
            cmd += self._common_args
            cmd += ('{0}:{1}'.format(host, in_path), out_path)
            indata = None
        else:
            cmd.append('sftp')
            cmd += self._common_args
            cmd.append(host)
            indata = "get {0} {1}\n".format(in_path, out_path)

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._send_password()
        stdout, stderr = p.communicate(indata)

        if p.returncode != 0:
            raise AnsibleError("failed to transfer file from {0}:\n{1}\n{2}".format(in_path, stdout, stderr))

    def close(self):
        ''' not applicable since we're executing openssh binaries '''
        self._connected = False

