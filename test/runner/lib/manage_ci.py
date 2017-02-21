"""Access Ansible Core CI remote services."""

from __future__ import absolute_import, print_function

import pipes

from time import sleep

import lib.pytar

from lib.util import (
    SubprocessError,
    ApplicationError,
    run_command,
)

from lib.core_ci import (
    AnsibleCoreCI,
)

from lib.ansible_util import (
    ansible_environment,
)


class ManageWindowsCI(object):
    """Manage access to a Windows instance provided by Ansible Core CI."""
    def __init__(self, core_ci):
        """
        :type core_ci: AnsibleCoreCI
        """
        self.core_ci = core_ci

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

        for _ in range(1, 120):
            try:
                run_command(self.core_ci.args, cmd, env=env)
                return
            except SubprocessError:
                sleep(10)
                continue

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))


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
            'ansible_user=%s' % self.core_ci.connection.username,
            'ansible_port=%s' % self.core_ci.connection.port,
            'ansible_connection=local',
            'ansible_ssh_private_key_file=%s' % self.core_ci.ssh_key.key,
            'ansible_network_os=%s' % self.core_ci.platform,
        ]

        name = '%s-%s' % (self.core_ci.platform, self.core_ci.version.replace('.', '_'))

        env = ansible_environment(self.core_ci.args)
        cmd = ['ansible', '-m', 'net_command', '-a', '?', '-i', '%s,' % name, name, '-e', ' '.join(extra_vars)]

        for _ in range(1, 90):
            try:
                run_command(self.core_ci.args, cmd, env=env)
                return
            except SubprocessError:
                sleep(10)
                continue

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))


class ManagePosixCI(object):
    """Manage access to a POSIX instance provided by Ansible Core CI."""
    def __init__(self, core_ci):
        """
        :type core_ci: AnsibleCoreCI
        """
        self.core_ci = core_ci
        self.ssh_args = ['-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', '-i', self.core_ci.ssh_key.key]

        if self.core_ci.platform == 'freebsd':
            self.become = ['su', '-l', 'root', '-c']
        elif self.core_ci.platform == 'osx':
            self.become = ['sudo', '-in', 'PATH=/usr/local/bin:$PATH']

    def setup(self):
        """Start instance and wait for it to become ready and respond to an ansible ping."""
        self.wait()
        self.configure()
        self.upload_source()

    def wait(self):
        """Wait for instance to respond to SSH."""
        for _ in range(1, 90):
            try:
                self.ssh('id')
                return
            except SubprocessError:
                sleep(10)
                continue

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))

    def configure(self):
        """Configure remote host for testing."""
        self.upload('test/runner/setup/remote.sh', '/tmp')
        self.ssh('chmod +x /tmp/remote.sh && /tmp/remote.sh %s' % self.core_ci.platform)

    def upload_source(self):
        """Upload and extract source."""
        if not self.core_ci.args.explain:
            lib.pytar.create_tarfile('/tmp/ansible.tgz', '.', lib.pytar.ignore)

        self.upload('/tmp/ansible.tgz', '/tmp')
        self.ssh('rm -rf ~/ansible && mkdir ~/ansible && cd ~/ansible && tar oxzf /tmp/ansible.tgz')

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

    def ssh(self, command):
        """
        :type command: str | list[str]
        """
        if isinstance(command, list):
            command = ' '.join(pipes.quote(c) for c in command)

        run_command(self.core_ci.args,
                    ['ssh', '-tt', '-q'] + self.ssh_args +
                    ['-p', str(self.core_ci.connection.port),
                     '%s@%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname)] +
                    self.become + [pipes.quote(command)])

    def scp(self, src, dst):
        """
        :type src: str
        :type dst: str
        """
        run_command(self.core_ci.args,
                    ['scp'] + self.ssh_args +
                    ['-P', str(self.core_ci.connection.port), '-q', '-r', src, dst])
