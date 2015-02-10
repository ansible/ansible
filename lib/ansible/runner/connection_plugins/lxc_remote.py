# (c) 2014, Gu1 <gu1@aeroxteam.fr>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

import functools
import pipes
import os.path

from ansible.runner.connection_plugins import ssh
from ansible import errors
from ansible import utils
from ansible.callbacks import vvv


def lxc_check(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        if self.lxc_name is None:
            raise errors.AnsibleError("to use the lxc_remote connection mode, you must specify a container name")
        return func(self, *args, **kwargs)
    return inner


class Connection(ssh.Connection):
    """
    Connection module for LXC containers located on a remote machine.

    This module inherits the ssh connection module.
    To use it, you could put something like this in your inventory:
    container_name ansible_ssh_user=user ansible_ssh_host=1.2.3.4 ansible_ssh_port=22 ansible_connection=lxc_remote

    Where "user" is the user you want to connect to on the lxc host using ssh,
    ansible_ssh_host and ansible_ssh_port are the host and port of the lxc host.
    If you specify a su or sudo_user, it will be used on the lxc host before running lxc-attach.
    """

    def __init__(self, *args, **kwargs):
        super(Connection, self).__init__(*args, **kwargs)
        self.delegate = None
        self.lxc_rootfs = None
        self.host_tmp_path = None

    @property
    def lxc_name(self):
        # set by the Runner class after connect() has been called
        return self.delegate

    def _lxc_cmd(self, cmd):
        return 'lxc-attach --name %s -- /bin/su %s -c %s' \
                % (pipes.quote(self.lxc_name),
                   pipes.quote(self.runner.remote_user),
                   pipes.quote(cmd))

    def _su_sudo_cmd(self, cmd):
        if self.runner.su and self.runner.su_user:
            return utils.make_su_cmd(self.runner.su_user, '/bin/sh', cmd)
        elif self.runner.sudo:
            return utils.make_sudo_cmd(self.runner.sudo_exe, self.runner.sudo_user, '/bin/sh', cmd)
        else:
            return cmd, None, None

    def connect(self):
        return super(Connection, self).connect()

    @lxc_check
    def exec_command(self, cmd, tmp_path, *args, **kwargs):
        kwargs['sudoable'] = True
        kwargs['su'] = True
        #if kwargs.get('sudoable', False) or kwargs.get('su', False):
        cmd = self._lxc_cmd(cmd)
        return super(Connection, self).exec_command(cmd, tmp_path, *args, **kwargs)

    @lxc_check
    def put_file(self, in_path, out_path):
        vvv("PUT %s TO %s" % (in_path, out_path), host=self.host)
        if not os.path.exists(in_path):
            raise errors.AnsibleFileNotFound("file or module does not exist: %s" % in_path)

        host = self.host
        if self.ipv6:
            host = '[%s]' % host

        remote_cmd, prompt, success_key = self._su_sudo_cmd(
            self._lxc_cmd('cat > %s; echo -n done' % pipes.quote(out_path))
        )

        cmd  = self._password_cmd()
        cmd += ['ssh'] + self.common_args + [host, remote_cmd]

        (p, stdin) = self._run(cmd, True)
        self._send_password()
        if (self.runner.sudo and self.runner.sudo_pass) or \
                (self.runner.su and self.runner.su_pass):
            (no_prompt_out, no_prompt_err) = self.send_su_sudo_password(p, stdin, success_key,
                                                                        True, prompt)

        com = self.CommunicateCallbacks(self.runner, open(in_path, 'r'),
                                        su=True, sudoable=True, prompt=prompt)
        returncode = self._communicate(p, stdin, callbacks=(com.stdin_cb, com.stdout_cb, com.stderr_cb))

        if com.stdout[-4:] != 'done':
            raise errors.AnsibleError("failed to transfer file to %s" % out_path)

        if returncode != 0:
            raise errors.AnsibleError("failed to transfer file to %s:\n%s\n%s" % (out_path, stdout, stderr))


    class FetchCommCB(ssh.Connection.CommunicateCallbacks):
        def __init__(self, *args, **kwargs):
            self.outfile = kwargs.pop('outfile')
            super(Connection.FetchCommCB, self).__init__(*args, **kwargs)

        def stdout_cb(self, data):
            # try to keep the last 4096 for check
            self.stdout += data
            self._check_for_su_sudo_fail(self.stdout)
            if len(self.stdout) > 4096:
                self.stdout = self.stdout[2048:]

            self.outfile.write(data)

    @lxc_check
    def fetch_file(self, in_path, out_path):
        vvv("FETCH %s TO %s" % (in_path, out_path), host=self.host)
        cmd = self._password_cmd()

        host = self.host
        if self.ipv6:
            host = '[%s]' % host

        remote_cmd, prompt, success_key = self._su_sudo_cmd(
            self._lxc_cmd('cat %s' % pipes.quote(in_path))
        )

        cmd  = self._password_cmd()
        cmd += ['ssh'] + self.common_args + [host, remote_cmd]

        (p, stdin) = self._run(cmd, True)
        self._send_password()
        if (self.runner.sudo and self.runner.sudo_pass) or \
                (self.runner.su and self.runner.su_pass):
            (no_prompt_out, no_prompt_err) = self.send_su_sudo_password(p, stdin, success_key,
                                                                        True, prompt)

        try:
            outfile = open(out_path, 'w')
        except IOError as e:
            raise errors.AnsibleError('could not open destination file %s: %s' % (out_path, e))

        com = self.FetchCommCB(self.runner, None, su=True, sudoable=True, prompt=prompt, outfile=outfile)
        returncode = self._communicate(p, stdin, callbacks=(com.stdin_cb, com.stdout_cb, com.stderr_cb))
        outfile.close()

        if p.returncode != 0:
            raise errors.AnsibleError("failed to transfer file from %s:\n%s\n%s" % (in_path, com.stdout, com.stderr))

    def close(self):
        return super(Connection, self).close()
