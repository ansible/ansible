"""Access Ansible Core CI remote services."""

from __future__ import absolute_import, print_function

import os
import tempfile
import time

import lib.pytar

from lib.util import (
    SubprocessError,
    ApplicationError,
    run_command,
    intercept_command,
    cmd_quote,
)

from lib.core_ci import (
    AnsibleCoreCI,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.config import (
    ShellConfig,
)


class ManageWindowsCI(object):
    """Manage access to a Windows instance provided by Ansible Core CI."""
    def __init__(self, core_ci):
        """
        :type core_ci: AnsibleCoreCI
        """
        self.core_ci = core_ci
        self.ssh_args = ['-i', self.core_ci.ssh_key.key]

        ssh_options = dict(
            BatchMode='yes',
            StrictHostKeyChecking='no',
            UserKnownHostsFile='/dev/null',
            ServerAliveInterval=15,
            ServerAliveCountMax=4,
        )

        for ssh_option in sorted(ssh_options):
            self.ssh_args += ['-o', '%s=%s' % (ssh_option, ssh_options[ssh_option])]

    def setup(self, python_version):
        """Used in delegate_remote to setup the host, no action is required for Windows.
        :type python_version: str
        """
        pass

    def wait(self):
        """Wait for instance to respond to ansible ping."""
        extra_vars = [
            'ansible_connection=winrm',
            'ansible_host=%s' % self.core_ci.connection.hostname,
            'ansible_user=%s' % self.core_ci.connection.username,
            'ansible_password=%s' % self.core_ci.connection.password,
            'ansible_port=%s' % self.core_ci.connection.port,
            'ansible_winrm_server_cert_validation=ignore',
        ]

        name = 'windows_%s' % self.core_ci.version

        env = ansible_environment(self.core_ci.args)
        cmd = ['ansible', '-m', 'win_ping', '-i', '%s,' % name, name, '-e', ' '.join(extra_vars)]

        for dummy in range(1, 120):
            try:
                intercept_command(self.core_ci.args, cmd, 'ping', env=env)
                return
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))

    def download(self, remote, local):
        """
        :type remote: str
        :type local: str
        """
        self.scp('%s@%s:%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname, remote), local)

    def upload(self, local, remote):
        """
        :type local: str
        :type remote: str
        """
        self.scp(local, '%s@%s:%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname, remote))

    def ssh(self, command, options=None, force_pty=True):
        """
        :type command: str | list[str]
        :type options: list[str] | None
        :type force_pty: bool
        """
        if not options:
            options = []
        if force_pty:
            options.append('-tt')

        if isinstance(command, list):
            command = ' '.join(cmd_quote(c) for c in command)

        run_command(self.core_ci.args,
                    ['ssh', '-q'] + self.ssh_args +
                    options +
                    ['-p', '22',
                     '%s@%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname)] +
                    [command])

    def scp(self, src, dst):
        """
        :type src: str
        :type dst: str
        """
        for dummy in range(1, 10):
            try:
                run_command(self.core_ci.args,
                            ['scp'] + self.ssh_args +
                            ['-P', '22', '-q', '-r', src, dst])
                return
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Failed transfer: %s -> %s' % (src, dst))


class ManageNetworkCI(object):
    """Manage access to a network instance provided by Ansible Core CI."""
    def __init__(self, core_ci):
        """
        :type core_ci: AnsibleCoreCI
        """
        self.core_ci = core_ci

    def wait(self):
        """Wait for instance to respond to ansible ping."""
        extra_vars = [
            'ansible_host=%s' % self.core_ci.connection.hostname,
            'ansible_port=%s' % self.core_ci.connection.port,
            'ansible_connection=local',
            'ansible_ssh_private_key_file=%s' % self.core_ci.ssh_key.key,
        ]

        name = '%s-%s' % (self.core_ci.platform, self.core_ci.version.replace('.', '-'))

        env = ansible_environment(self.core_ci.args)
        cmd = [
            'ansible',
            '-m', '%s_command' % self.core_ci.platform,
            '-a', 'commands=?',
            '-u', self.core_ci.connection.username,
            '-i', '%s,' % name,
            '-e', ' '.join(extra_vars),
            name,
        ]

        for dummy in range(1, 90):
            try:
                intercept_command(self.core_ci.args, cmd, 'ping', env=env)
                return
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))


class ManagePosixCI(object):
    """Manage access to a POSIX instance provided by Ansible Core CI."""
    def __init__(self, core_ci):
        """
        :type core_ci: AnsibleCoreCI
        """
        self.core_ci = core_ci
        self.ssh_args = ['-i', self.core_ci.ssh_key.key]

        ssh_options = dict(
            BatchMode='yes',
            StrictHostKeyChecking='no',
            UserKnownHostsFile='/dev/null',
            ServerAliveInterval=15,
            ServerAliveCountMax=4,
        )

        for ssh_option in sorted(ssh_options):
            self.ssh_args += ['-o', '%s=%s' % (ssh_option, ssh_options[ssh_option])]

        if self.core_ci.platform == 'freebsd':
            if self.core_ci.provider == 'aws':
                self.become = ['su', '-l', 'root', '-c']
            elif self.core_ci.provider == 'azure':
                self.become = ['sudo', '-in', 'sh', '-c']
            else:
                raise NotImplementedError('provider %s has not been implemented' % self.core_ci.provider)
        elif self.core_ci.platform == 'osx':
            self.become = ['sudo', '-in', 'PATH=/usr/local/bin:$PATH']
        elif self.core_ci.platform == 'rhel':
            self.become = ['sudo', '-in', 'bash', '-c']

    def setup(self, python_version):
        """Start instance and wait for it to become ready and respond to an ansible ping.
        :type python_version: str
        """
        self.wait()

        if isinstance(self.core_ci.args, ShellConfig):
            if self.core_ci.args.raw:
                return

        self.configure(python_version)
        self.upload_source()

    def wait(self):
        """Wait for instance to respond to SSH."""
        for dummy in range(1, 90):
            try:
                self.ssh('id')
                return
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))

    def configure(self, python_version):
        """Configure remote host for testing.
        :type python_version: str
        """
        self.upload('test/runner/setup/remote.sh', '/tmp')
        self.ssh('chmod +x /tmp/remote.sh && /tmp/remote.sh %s %s' % (self.core_ci.platform, python_version))

    def upload_source(self):
        """Upload and extract source."""
        with tempfile.NamedTemporaryFile(prefix='ansible-source-', suffix='.tgz') as local_source_fd:
            remote_source_dir = '/tmp'
            remote_source_path = os.path.join(remote_source_dir, os.path.basename(local_source_fd.name))

            if not self.core_ci.args.explain:
                lib.pytar.create_tarfile(local_source_fd.name, '.', lib.pytar.DefaultTarFilter())

            self.upload(local_source_fd.name, remote_source_dir)
            self.ssh('rm -rf ~/ansible && mkdir ~/ansible && cd ~/ansible && tar oxzf %s' % remote_source_path)

    def download(self, remote, local):
        """
        :type remote: str
        :type local: str
        """
        self.scp('%s@%s:%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname, remote), local)

    def upload(self, local, remote):
        """
        :type local: str
        :type remote: str
        """
        self.scp(local, '%s@%s:%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname, remote))

    def ssh(self, command, options=None):
        """
        :type command: str | list[str]
        :type options: list[str] | None
        """
        if not options:
            options = []

        if isinstance(command, list):
            command = ' '.join(cmd_quote(c) for c in command)

        run_command(self.core_ci.args,
                    ['ssh', '-tt', '-q'] + self.ssh_args +
                    options +
                    ['-p', str(self.core_ci.connection.port),
                     '%s@%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname)] +
                    self.become + [cmd_quote(command)])

    def scp(self, src, dst):
        """
        :type src: str
        :type dst: str
        """
        for dummy in range(1, 10):
            try:
                run_command(self.core_ci.args,
                            ['scp'] + self.ssh_args +
                            ['-P', str(self.core_ci.connection.port), '-q', '-r', src, dst])
                return
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Failed transfer: %s -> %s' % (src, dst))
