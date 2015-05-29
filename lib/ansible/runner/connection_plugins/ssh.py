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
        self.user = str(user)
        self.password = password
        self.private_key_file = private_key_file
        self.HASHED_KEY_MAGIC = "|1|"
        self.has_pipelining = True

        # TODO: add pbrun, pfexec
        self.become_methods_supported=['sudo', 'su', 'pbrun']

        fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_EX)
        self.cp_dir = utils.prepare_writeable_dir('$HOME/.ansible/cp',mode=0700)
        fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_UN)

    def connect(self):
        ''' connect to the remote host '''

        vvv("ESTABLISH CONNECTION FOR USER: %s" % self.user, host=self.host)

        self.common_args = []
        extra_args = C.ANSIBLE_SSH_ARGS
        if extra_args is not None:
            # make sure there is no empty string added as this can produce weird errors
            self.common_args += [x.strip() for x in shlex.split(extra_args) if x.strip()]
        else:
            self.common_args += ["-o", "ControlMaster=auto",
                                 "-o", "ControlPersist=60s",
                                 "-o", "ControlPath=\"%s\"" % (C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self.cp_dir))]

        cp_in_use = False
        cp_path_set = False
        for arg in self.common_args:
            if "ControlPersist" in arg:
                cp_in_use = True
            if "ControlPath" in arg:
                cp_path_set = True

        if cp_in_use and not cp_path_set:
            self.common_args += ["-o", "ControlPath=\"%s\"" % (C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self.cp_dir))]

        if not C.HOST_KEY_CHECKING:
            self.common_args += ["-o", "StrictHostKeyChecking=no"]

        if self.port is not None:
            self.common_args += ["-o", "Port=%d" % (self.port)]
        if self.private_key_file is not None:
            self.common_args += ["-o", "IdentityFile=\"%s\"" % os.path.expanduser(self.private_key_file)]
        elif self.runner.private_key_file is not None:
            self.common_args += ["-o", "IdentityFile=\"%s\"" % os.path.expanduser(self.runner.private_key_file)]
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

    def _run(self, cmd, indata):
        if indata:
            # do not use pseudo-pty
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdin = p.stdin
        else:
            # try to use upseudo-pty
            try:
                # Make sure stdin is a proper (pseudo) pty to avoid: tcgetattr errors
                master, slave = pty.openpty()
                p = subprocess.Popen(cmd, stdin=slave,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = os.fdopen(master, 'w', 0)
                os.close(slave)
            except:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = p.stdin

        return (p, stdin)

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

    def _communicate(self, p, stdin, indata, sudoable=False, prompt=None):
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
                raise errors.AnsibleError('SSH Error: data could not be sent to the remote host. Make sure this host can be reached over ssh')
        # Read stdout/stderr from process
        while True:
            rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

            # fail early if the become password is wrong
            if self.runner.become and sudoable:
                incorrect_password = gettext.dgettext(self.runner.become_method, C.BECOME_ERROR_STRINGS[self.runner.become_method])

                if prompt:
                    if self.runner.become_pass:
                        if stdout.endswith("%s\r\n%s" % (incorrect_password, prompt)):
                            raise errors.AnsibleError('Incorrect become password')

                    if stdout.endswith(prompt):
                        raise errors.AnsibleError('Missing become password')
                    elif stdout.endswith("%s\r\n%s" % (incorrect_password, prompt)):
                        raise errors.AnsibleError('Incorrect become password')

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
            except IOError, e:
                hfiles_not_found += 1
                continue
            else:
                data = host_fh.read()
                host_fh.close()
                
            for line in data.split("\n"):
                line = line.strip()
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
            vvv("EXEC previous known host file not found for %s" % host)
        return True

    def exec_command(self, cmd, tmp_path, become_user=None, sudoable=False, executable='/bin/sh', in_data=None):
        ''' run a command on the remote host '''

        if sudoable and self.runner.become and self.runner.become_method not in self.become_methods_supported:
            raise errors.AnsibleError("Internal Error: this module does not support running commands via %s" % self.runner.become_method)

        ssh_cmd = self._password_cmd()
        ssh_cmd += ["ssh", "-C"]
        if not in_data:
            # we can only use tty when we are not pipelining the modules. piping data into /usr/bin/python
            # inside a tty automatically invokes the python interactive-mode but the modules are not
            # compatible with the interactive-mode ("unexpected indent" mainly because of empty lines)
            ssh_cmd += ["-tt"]
        if utils.VERBOSITY > 3:
            ssh_cmd += ["-vvv"]
        else:
            if self.runner.module_name == 'raw':
                ssh_cmd += ["-q"]
            else:
                ssh_cmd += ["-v"]
        ssh_cmd += self.common_args

        if self.ipv6:
            ssh_cmd += ['-6']
        ssh_cmd += [self.host]

        if self.runner.become and sudoable:
            becomecmd, prompt, success_key = utils.make_become_cmd(cmd, become_user, executable, self.runner.become_method, '', self.runner.become_exe)
            ssh_cmd.append(becomecmd)
        else:
            prompt = None
            if executable:
                ssh_cmd.append(executable + ' -c ' + pipes.quote(cmd))
            else:
                ssh_cmd.append(cmd)

        vvv("EXEC %s" % ' '.join(ssh_cmd), host=self.host)

        not_in_host_file = self.not_in_host_file(self.host)

        if C.HOST_KEY_CHECKING and not_in_host_file:
            # lock around the initial SSH connectivity so the user prompt about whether to add
            # the host to known hosts is not intermingled with multiprocess output.
            fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_EX)
            fcntl.lockf(self.runner.output_lockfile, fcntl.LOCK_EX)

        # create process
        (p, stdin) = self._run(ssh_cmd, in_data)

        self._send_password()

        no_prompt_out = ''
        no_prompt_err = ''
        if sudoable and self.runner.become and self.runner.become_pass:
            # several cases are handled for escalated privileges with password
            # * NOPASSWD (tty & no-tty): detect success_key on stdout
            # * without NOPASSWD:
            #   * detect prompt on stdout (tty)
            #   * detect prompt on stderr (no-tty)
            fcntl.fcntl(p.stdout, fcntl.F_SETFL,
                        fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL,
                        fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)
            become_output = ''
            become_errput = ''

            while True:
                if success_key in become_output or \
                    (prompt and become_output.endswith(prompt)) or \
                    utils.su_prompts.check_su_prompt(become_output):
                    break

                rfd, wfd, efd = select.select([p.stdout, p.stderr], [],
                                              [p.stdout], self.runner.timeout)
                if p.stderr in rfd:
                    chunk = p.stderr.read()
                    if not chunk:
                        raise errors.AnsibleError('ssh connection closed waiting for a privilege escalation password prompt')
                    become_errput += chunk
                    incorrect_password = gettext.dgettext(
                        "become", "Sorry, try again.")
                    if become_errput.strip().endswith("%s%s" % (prompt, incorrect_password)):
                        raise errors.AnsibleError('Incorrect become password')
                    elif prompt and become_errput.endswith(prompt):
                        stdin.write(self.runner.become_pass + '\n')

                if p.stdout in rfd:
                    chunk = p.stdout.read()
                    if not chunk:
                        raise errors.AnsibleError('ssh connection closed waiting for %s password prompt' % self.runner.become_method)
                    become_output += chunk

                if not rfd:
                    # timeout. wrap up process communication
                    stdout = p.communicate()
                    raise errors.AnsibleError('ssh connection error while waiting for %s password prompt' % self.runner.become_method)

            if success_key in become_output:
                no_prompt_out += become_output
                no_prompt_err += become_errput
            elif sudoable:
                stdin.write(self.runner.become_pass + '\n')

        (returncode, stdout, stderr) = self._communicate(p, stdin, in_data, sudoable=sudoable, prompt=prompt)

        if C.HOST_KEY_CHECKING and not_in_host_file:
            # lock around the initial SSH connectivity so the user prompt about whether to add 
            # the host to known hosts is not intermingled with multiprocess output.
            fcntl.lockf(self.runner.output_lockfile, fcntl.LOCK_UN)
            fcntl.lockf(self.runner.process_lockfile, fcntl.LOCK_UN)
        controlpersisterror = 'Bad configuration option: ControlPersist' in stderr or \
                              'unknown configuration option: ControlPersist' in stderr

        if C.HOST_KEY_CHECKING:
            if ssh_cmd[0] == "sshpass" and p.returncode == 6:
                raise errors.AnsibleError('Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support this.  Please add this host\'s fingerprint to your known_hosts file to manage this host.')

        if p.returncode != 0 and controlpersisterror:
            raise errors.AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" (or ssh_args in [ssh_connection] section of the config file) before running again')
        if p.returncode == 255 and (in_data or self.runner.module_name == 'raw'):
            raise errors.AnsibleError('SSH Error: data could not be sent to the remote host. Make sure this host can be reached over ssh')
        if p.returncode == 255:
            ip = None
            port = None
            for line in stderr.splitlines():
                match = re.search(
                    'Connecting to .*\[(\d+\.\d+\.\d+\.\d+)\] port (\d+)',
                    line)
                if match:
                    ip = match.group(1)
                    port = match.group(2)
            if 'UNPROTECTED PRIVATE KEY FILE' in stderr:
                lines = [line for line in stderr.splitlines()
                         if 'ignore key:' in line]
            else:
                lines = stderr.splitlines()[-1:]
            if ip and port:
                lines.append('    while connecting to %s:%s' % (ip, port))
            lines.append(
                'It is sometimes useful to re-run the command using -vvvv, '
                'which prints SSH debug output to help diagnose the issue.')
            raise errors.AnsibleError('SSH Error: %s' % '\n'.join(lines))

        return (p.returncode, '', no_prompt_out + stdout, no_prompt_err + stderr)

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

        (p, stdin) = self._run(cmd, indata)

        self._send_password()

        (returncode, stdout, stderr) = self._communicate(p, stdin, indata)

        if returncode != 0:
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

