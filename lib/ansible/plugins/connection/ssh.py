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

import fcntl
import os
import pipes
import pty
import pwd
import select
import shlex
import subprocess
import time

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.plugins.connection import ConnectionBase
from ansible.utils.path import unfrackpath, makedirs_safe

SSHPASS_AVAILABLE = None

class Connection(ConnectionBase):
    ''' ssh based connections '''

    transport = 'ssh'
    has_pipelining = True
    become_methods = frozenset(C.BECOME_METHODS).difference(['runas'])

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)

        self.host = self._play_context.remote_addr
        self.ssh_extra_args = ''
        self.ssh_args = ''

    def set_host_overrides(self, host):
        v = host.get_vars()
        if 'ansible_ssh_extra_args' in v:
            self.ssh_extra_args = v['ansible_ssh_extra_args']
        if 'ansible_ssh_args' in v:
            self.ssh_args = v['ansible_ssh_args']

    # The connection is created by running ssh/scp/sftp from the exec_command,
    # put_file, and fetch_file methods, so we don't need to do any connection
    # management here.

    def _connect(self):
        self._connected = True
        return self

    def close(self):
        # If we have a persistent ssh connection (ControlPersist), we can ask it
        # to stop listening. Otherwise, there's nothing to do here.

        # TODO: reenable once winrm issues are fixed
        # temporarily disabled as we are forced to currently close connections after every task because of winrm
        # if self._connected and self._persistent:
        #     cmd = self._build_command('ssh', '-O', 'stop', self.host)
        #     p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #     stdout, stderr = p.communicate()

        self._connected = False

    def _build_command(self, binary, *other_args):
        '''
        Takes a binary (ssh, scp, sftp) and optional extra arguments and returns
        a command line as an array that can be passed to subprocess.Popen after
        appending any extra commands to it.
        '''

        self._command = []

        ## First, the command name.

        # If we want to use password authentication, we have to set up a pipe to
        # write the password to sshpass.

        if self._play_context.password:
            global SSHPASS_AVAILABLE

            # We test once if sshpass is available, and remember the result. It
            # would be nice to use distutils.spawn.find_executable for this, but
            # distutils isn't always available; shutils.which() is Python3-only.

            if SSHPASS_AVAILABLE is None:
                try:
                    p = subprocess.Popen(["sshpass"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p.communicate()
                    SSHPASS_AVAILABLE = True
                except OSError:
                    SSHPASS_AVAILABLE = False

            if not SSHPASS_AVAILABLE:
                raise AnsibleError("to use the 'ssh' connection type with passwords, you must install the sshpass program")

            self.sshpass_pipe = os.pipe()
            self._command += ['sshpass', '-d{0}'.format(self.sshpass_pipe[0])]

        self._command += [binary]

        ## Next, additional arguments based on the configuration.

        # sftp batch mode allows us to correctly catch failed transfers, but can
        # be disabled if the client side doesn't support the option. FIXME: is
        # this still a real concern?

        if binary == 'sftp' and C.DEFAULT_SFTP_BATCH_MODE:
            self._command += ['-b', '-']

        elif binary == 'ssh':
            self._command += ['-C']

        self._command += ['-vvv']

        # Next, we add ansible_ssh_args from the inventory if it's set, or
        # [ssh_connection]ssh_args from ansible.cfg, or the default Control*
        # settings.

        if self.ssh_args:
            args = self._split_args(self.ssh_args)
            self.add_args("inventory set ansible_ssh_args", args)
        elif C.ANSIBLE_SSH_ARGS:
            args = self._split_args(C.ANSIBLE_SSH_ARGS)
            self.add_args("ansible.cfg set ssh_args", args)
        else:
            args = (
                "-o", "ControlMaster=auto",
                "-o", "ControlPersist=60s"
            )
            self.add_args("default arguments", args)

        # Now we add various arguments controlled by configuration file settings
        # (e.g. host_key_checking) or inventory variables (ansible_ssh_port) or
        # a combination thereof.

        if not C.HOST_KEY_CHECKING:
            self.add_args(
                "ANSIBLE_HOST_KEY_CHECKING/host_key_checking disabled",
                ("-o", "StrictHostKeyChecking=no")
            )

        if self._play_context.port is not None:
            self.add_args(
                "ANSIBLE_REMOTE_PORT/remote_port/ansible_ssh_port set",
                ("-o", "Port={0}".format(self._play_context.port))
            )

        key = self._play_context.private_key_file
        if key:
            self.add_args(
                "ANSIBLE_PRIVATE_KEY_FILE/private_key_file/ansible_ssh_private_key_file set",
                ("-o", "IdentityFile=\"{0}\"".format(os.path.expanduser(key)))
            )

        if not self._play_context.password:
            self.add_args(
                "ansible_password/ansible_ssh_pass not set", (
                    "-o", "KbdInteractiveAuthentication=no",
                    "-o", "PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey",
                    "-o", "PasswordAuthentication=no"
                )
            )

        user = self._play_context.remote_user
        if user and user != pwd.getpwuid(os.geteuid())[0]:
            self.add_args(
                "ANSIBLE_REMOTE_USER/remote_user/ansible_ssh_user/user/-u set",
                ("-o", "User={0}".format(self._play_context.remote_user))
            )

        self.add_args(
            "ANSIBLE_TIMEOUT/timeout set",
            ("-o", "ConnectTimeout={0}".format(self._play_context.timeout))
        )

        # If any extra SSH arguments are specified in the inventory for
        # this host, or specified as an override on the command line,
        # add them in.

        if self._play_context.ssh_extra_args:
            args = self._split_args(self._play_context.ssh_extra_args)
            self.add_args("command-line added --ssh-extra-args", args)
        elif self.ssh_extra_args:
            args = self._split_args(self.ssh_extra_args)
            self.add_args("inventory added ansible_ssh_extra_args", args)

        # If ssh_args or ssh_extra_args set ControlPersist but not a
        # ControlPath, add one ourselves.

        cp_in_use = False
        cp_path_set = False
        for arg in self._command:
            if "ControlPersist" in arg:
                cp_in_use = True
            if "ControlPath" in arg:
                cp_path_set = True

        if cp_in_use and not cp_path_set:
            self._cp_dir = unfrackpath('$HOME/.ansible/cp')

            args = ("-o", "ControlPath={0}".format(
                C.ANSIBLE_SSH_CONTROL_PATH % dict(directory=self._cp_dir))
            )
            self.add_args("found only ControlPersist; added ControlPath", args)

            # The directory must exist and be writable.
            makedirs_safe(self._cp_dir, 0o700)
            if not os.access(self._cp_dir, os.W_OK):
                raise AnsibleError("Cannot write to ControlPath %s" % self._cp_dir)

        # If the configuration dictates that we use a persistent connection,
        # then we remember that for later. (We could be more thorough about
        # detecting this, though.)

        if cp_in_use:
            self._persistent = True

        ## Finally, we add any caller-supplied extras.

        if other_args:
            self._command += other_args

        return self._command

    def exec_command(self, *args, **kwargs):
        """
        Wrapper around _exec_command to retry in the case of an ssh failure

        Will retry if:
        * an exception is caught
        * ssh returns 255
        Will not retry if
        * remaining_tries is <2
        * retries limit reached
        """

        remaining_tries = int(C.ANSIBLE_SSH_RETRIES) + 1
        cmd_summary = "%s..." % args[0]
        for attempt in xrange(remaining_tries):
            try:
                return_tuple = self._exec_command(*args, **kwargs)
                # 0 = success
                # 1-254 = remote command return code
                # 255 = failure from the ssh command itself
                if return_tuple[0] != 255 or attempt == (remaining_tries - 1):
                    break
                else:
                    raise AnsibleConnectionFailure("Failed to connect to the host via ssh.")
            except (AnsibleConnectionFailure, Exception) as e:
                if attempt == remaining_tries - 1:
                    raise e
                else:
                    pause = 2 ** attempt - 1
                    if pause > 30:
                        pause = 30

                    if isinstance(e, AnsibleConnectionFailure):
                        msg = "ssh_retry: attempt: %d, ssh return code is 255. cmd (%s), pausing for %d seconds" % (attempt, cmd_summary, pause)
                    else:
                        msg = "ssh_retry: attempt: %d, caught exception(%s) from cmd (%s), pausing for %d seconds" % (attempt, e, cmd_summary, pause)

                    self._display.vv(msg)

                    time.sleep(pause)
                    continue

        return return_tuple

    def _exec_command(self, cmd, tmp_path, in_data=None, sudoable=True):
        ''' run a command on the remote host '''

        super(Connection, self).exec_command(cmd, tmp_path, in_data=in_data, sudoable=sudoable)

        self._display.vvv("ESTABLISH SSH CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)

        # we can only use tty when we are not pipelining the modules. piping
        # data into /usr/bin/python inside a tty automatically invokes the
        # python interactive-mode but the modules are not compatible with the
        # interactive-mode ("unexpected indent" mainly because of empty lines)

        if in_data:
            cmd = self._build_command('ssh', self.host, cmd)
        else:
            cmd = self._build_command('ssh', '-tt', self.host, cmd)

        (returncode, stdout, stderr) = self._run(cmd, in_data, sudoable=sudoable)

        return (returncode, '', stdout, stderr)

    def put_file(self, in_path, out_path):
        ''' transfer a file from local to remote '''

        super(Connection, self).put_file(in_path, out_path)

        self._display.vvv("PUT {0} TO {1}".format(in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(in_path))

        # scp and sftp require square brackets for IPv6 addresses, but
        # accept them for hostnames and IPv4 addresses too.
        host = '[%s]' % self.host

        if C.DEFAULT_SCP_IF_SSH:
            cmd = self._build_command('scp', in_path, '{0}:{1}'.format(host, pipes.quote(out_path)))
            in_data = None
        else:
            cmd = self._build_command('sftp', host)
            in_data = "put {0} {1}\n".format(pipes.quote(in_path), pipes.quote(out_path))

        (returncode, stdout, stderr) = self._run(cmd, in_data)

        if returncode != 0:
            raise AnsibleError("failed to transfer file to {0}:\n{1}\n{2}".format(out_path, stdout, stderr))

    def fetch_file(self, in_path, out_path):
        ''' fetch a file from remote to local '''

        super(Connection, self).fetch_file(in_path, out_path)

        self._display.vvv("FETCH {0} TO {1}".format(in_path, out_path), host=self.host)

        # scp and sftp require square brackets for IPv6 addresses, but
        # accept them for hostnames and IPv4 addresses too.
        host = '[%s]' % self.host

        if C.DEFAULT_SCP_IF_SSH:
            cmd = self._build_command('scp', '{0}:{1}'.format(host, pipes.quote(in_path)), out_path)
            in_data = None
        else:
            cmd = self._build_command('sftp', host)
            in_data = "get {0} {1}\n".format(pipes.quote(in_path), pipes.quote(out_path))

        (returncode, stdout, stderr) = self._run(cmd, in_data)

        if returncode != 0:
            raise AnsibleError("failed to transfer file from {0}:\n{1}\n{2}".format(in_path, stdout, stderr))

    def _run(self, cmd, in_data, sudoable=True):
        '''
        Starts the command and communicates with it until it ends.
        '''

        display_cmd = map(pipes.quote, cmd[:-1]) + [cmd[-1]]
        self._display.vvv('SSH: EXEC {0}'.format(' '.join(display_cmd)), host=self.host)

        # Start the given command. If we don't need to pipeline data, we can try
        # to use a pseudo-tty. If we are pipelining data, or can't create a pty,
        # we fall back to using plain old pipes.

        p = None
        if not in_data:
            try:
                # Make sure stdin is a proper pty to avoid tcgetattr errors
                master, slave = pty.openpty()
                p = subprocess.Popen(cmd, stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdin = os.fdopen(master, 'w', 0)
                os.close(slave)
            except:
                p = None

        if not p:
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdin = p.stdin

        # If we are using SSH password authentication, write the password to the
        # pipe we opened in _build_command.

        if self._play_context.password:
            os.close(self.sshpass_pipe[0])
            os.write(self.sshpass_pipe[1], "{0}\n".format(self._play_context.password))
            os.close(self.sshpass_pipe[1])

        # This section is specific to ssh:
        #
        # If we have a privilege escalation prompt, we need to look for the
        # prompt and send the password (but we won't be prompted if sudo has
        # NOPASSWD configured), then detect successful escalation (or handle
        # errors and timeouts).

        no_prompt_out = ''
        no_prompt_err = ''

        if self._play_context.prompt:
            self._display.debug("Handling privilege escalation password prompt.")

            fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) | os.O_NONBLOCK)
            fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) | os.O_NONBLOCK)

            become_output = ''
            become_errput = ''
            passprompt = False

            while True:
                self._display.debug('Waiting for Privilege Escalation input')

                if self.check_become_success(become_output + become_errput):
                    self._display.debug('Succeded!')
                    break
                elif self.check_password_prompt(become_output) or self.check_password_prompt(become_errput):
                    self._display.debug('Password prompt!')
                    passprompt = True
                    break

                self._display.debug('Read next chunks')
                rfd, wfd, efd = select.select([p.stdout, p.stderr], [], [p.stdout], self._play_context.timeout)
                if not rfd:
                    # timeout. wrap up process communication
                    stdout, stderr = p.communicate()
                    raise AnsibleError('Connection error waiting for privilege escalation password prompt: %s' % become_output)

                elif p.stderr in rfd:
                    chunk = p.stderr.read()
                    become_errput += chunk
                    self._display.debug('stderr chunk is: %s' % chunk)
                    self.check_incorrect_password(become_errput)

                elif p.stdout in rfd:
                    chunk = p.stdout.read()
                    become_output += chunk
                    self._display.debug('stdout chunk is: %s' % chunk)

                if not chunk:
                    break
                    #raise AnsibleError('Connection closed waiting for privilege escalation password prompt: %s ' % become_output)

            if passprompt:
                self._display.debug("Sending privilege escalation password.")
                stdin.write(self._play_context.become_pass + '\n')
            else:
                no_prompt_out = become_output
                no_prompt_err = become_errput

        # Now we're back to common handling for ssh/scp/sftp. If we have any
        # data to write into the connection, we do it now. (But we can't use
        # p.communicate because the ControlMaster may have stdout open too.)

        fcntl.fcntl(p.stdout, fcntl.F_SETFL, fcntl.fcntl(p.stdout, fcntl.F_GETFL) & ~os.O_NONBLOCK)
        fcntl.fcntl(p.stderr, fcntl.F_SETFL, fcntl.fcntl(p.stderr, fcntl.F_GETFL) & ~os.O_NONBLOCK)

        if in_data:
            try:
                stdin.write(in_data)
                stdin.close()
            except:
                raise AnsibleConnectionFailure('SSH Error: data could not be sent to the remote host. Make sure this host can be reached over ssh')

        # Now we just loop reading stdout/stderr from the process until it
        # terminates.

        stdout = stderr = ''
        rpipes = [p.stdout, p.stderr]

        while True:
            rfd, wfd, efd = select.select(rpipes, [], rpipes, 1)

            # fail early if the become password is wrong
            if self._play_context.become and sudoable:
                if self._play_context.become_pass:
                    self.check_incorrect_password(stdout)
                elif self.check_password_prompt(stdout):
                    raise AnsibleError('Missing %s password' % self._play_context.become_method)

            if p.stderr in rfd:
                dat = os.read(p.stderr.fileno(), 9000)
                stderr += dat
                if dat == '':
                    rpipes.remove(p.stderr)
            elif p.stdout in rfd:
                dat = os.read(p.stdout.fileno(), 9000)
                stdout += dat
                if dat == '':
                    rpipes.remove(p.stdout)

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

        controlpersisterror = 'Bad configuration option: ControlPersist' in stderr or 'unknown configuration option: ControlPersist' in stderr

        if C.HOST_KEY_CHECKING:
            if cmd[0] == "sshpass" and p.returncode == 6:
                raise AnsibleError('Using a SSH password instead of a key is not possible because Host Key checking is enabled and sshpass does not support this.  Please add this host\'s fingerprint to your known_hosts file to manage this host.')

        if p.returncode != 0 and controlpersisterror:
            raise AnsibleError('using -c ssh on certain older ssh versions may not support ControlPersist, set ANSIBLE_SSH_ARGS="" (or ssh_args in [ssh_connection] section of the config file) before running again')
        # FIXME: module name isn't in runner
        #if p.returncode == 255 and (in_data or self.runner.module_name == 'raw'):
        if p.returncode == 255 and in_data:
            raise AnsibleConnectionFailure('SSH Error: data could not be sent to the remote host. Make sure this host can be reached over ssh')

        return (p.returncode, no_prompt_out+stdout, no_prompt_err+stderr)

    # Utility functions

    def _split_args(self, argstring):
        """
        Takes a string like '-o Foo=1 -o Bar="foo bar"' and returns a
        list ['-o', 'Foo=1', '-o', 'Bar=foo bar'] that can be added to
        the argument list. The list will not contain any empty elements.
        """
        return [x.strip() for x in shlex.split(argstring) if x.strip()]

    def add_args(self, explanation, args):
        """
        Adds the given args to self._command and displays a caller-supplied
        explanation of why they were added.
        """
        self._command += args
        self._display.vvvvv('SSH: ' + explanation + ': (%s)' % ')('.join(args), host=self._play_context.remote_addr)
