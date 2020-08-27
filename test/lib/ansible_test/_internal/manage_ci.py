"""Access Ansible Core CI remote services."""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import tempfile
import time

from .util import (
    SubprocessError,
    ApplicationError,
    cmd_quote,
    display,
    ANSIBLE_TEST_DATA_ROOT,
)

from .util_common import (
    intercept_command,
    get_network_settings,
    run_command,
)

from .core_ci import (
    AnsibleCoreCI,
)

from .ansible_util import (
    ansible_environment,
)

from .config import (
    ShellConfig,
)

from .payload import (
    create_payload,
)


class ManageWindowsCI:
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
        cmd = ['ansible', '-m', 'ansible.windows.win_ping', '-i', '%s,' % name, name, '-e', ' '.join(extra_vars)]

        for dummy in range(1, 120):
            try:
                intercept_command(self.core_ci.args, cmd, 'ping', env=env, disable_coverage=True)
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


class ManageNetworkCI:
    """Manage access to a network instance provided by Ansible Core CI."""
    def __init__(self, core_ci):
        """
        :type core_ci: AnsibleCoreCI
        """
        self.core_ci = core_ci

    def wait(self):
        """Wait for instance to respond to ansible ping."""
        settings = get_network_settings(self.core_ci.args, self.core_ci.platform, self.core_ci.version)

        extra_vars = [
            'ansible_host=%s' % self.core_ci.connection.hostname,
            'ansible_port=%s' % self.core_ci.connection.port,
            'ansible_ssh_private_key_file=%s' % self.core_ci.ssh_key.key,
        ] + [
            '%s=%s' % (key, value) for key, value in settings.inventory_vars.items()
        ]

        name = '%s-%s' % (self.core_ci.platform, self.core_ci.version.replace('.', '-'))

        env = ansible_environment(self.core_ci.args)
        cmd = [
            'ansible',
            '-m', '%s%s_command' % (settings.collection + '.' if settings.collection else '', self.core_ci.platform),
            '-a', 'commands=?',
            '-u', self.core_ci.connection.username,
            '-i', '%s,' % name,
            '-e', ' '.join(extra_vars),
            name,
        ]

        for dummy in range(1, 90):
            try:
                intercept_command(self.core_ci.args, cmd, 'ping', env=env, disable_coverage=True)
                return
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))


class ManagePosixCI:
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
        elif self.core_ci.platform == 'macos':
            self.become = ['sudo', '-in', 'PATH=/usr/local/bin:$PATH', 'sh', '-c']
        elif self.core_ci.platform == 'osx':
            self.become = ['sudo', '-in', 'PATH=/usr/local/bin:$PATH']
        elif self.core_ci.platform == 'rhel' or self.core_ci.platform == 'centos':
            self.become = ['sudo', '-in', 'bash', '-c']
        elif self.core_ci.platform in ['aix', 'ibmi']:
            self.become = []

    def setup(self, python_version):
        """Start instance and wait for it to become ready and respond to an ansible ping.
        :type python_version: str
        :rtype: str
        """
        pwd = self.wait()

        display.info('Remote working directory: %s' % pwd, verbosity=1)

        if isinstance(self.core_ci.args, ShellConfig):
            if self.core_ci.args.raw:
                return pwd

        self.configure(python_version)
        self.upload_source()

        return pwd

    def wait(self):  # type: () -> str
        """Wait for instance to respond to SSH."""
        for dummy in range(1, 90):
            try:
                stdout = self.ssh('pwd', capture=True)[0]

                if self.core_ci.args.explain:
                    return '/pwd'

                pwd = stdout.strip().splitlines()[-1]

                if not pwd.startswith('/'):
                    raise Exception('Unexpected current working directory "%s" from "pwd" command output:\n%s' % (pwd, stdout))

                return pwd
            except SubprocessError:
                time.sleep(10)

        raise ApplicationError('Timeout waiting for %s/%s instance %s.' %
                               (self.core_ci.platform, self.core_ci.version, self.core_ci.instance_id))

    def configure(self, python_version):
        """Configure remote host for testing.
        :type python_version: str
        """
        self.upload(os.path.join(ANSIBLE_TEST_DATA_ROOT, 'setup', 'remote.sh'), '/tmp')
        self.ssh('chmod +x /tmp/remote.sh && /tmp/remote.sh %s %s' % (self.core_ci.platform, python_version))

    def upload_source(self):
        """Upload and extract source."""
        with tempfile.NamedTemporaryFile(prefix='ansible-source-', suffix='.tgz') as local_source_fd:
            remote_source_dir = '/tmp'
            remote_source_path = os.path.join(remote_source_dir, os.path.basename(local_source_fd.name))

            create_payload(self.core_ci.args, local_source_fd.name)

            self.upload(local_source_fd.name, remote_source_dir)
            # AIX does not provide the GNU tar version, leading to parameters
            # being different and -z not being recognized. This pattern works
            # with both versions of tar.
            self.ssh(
                'rm -rf ~/ansible ~/ansible_collections && cd ~/ && gunzip --stdout %s | tar oxf - && rm %s' %
                (remote_source_path, remote_source_path)
            )

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

    def ssh(self, command, options=None, capture=False):
        """
        :type command: str | list[str]
        :type options: list[str] | None
        :type capture: bool
        :rtype: str | None, str | None
        """
        if not options:
            options = []

        if isinstance(command, list):
            command = ' '.join(cmd_quote(c) for c in command)

        command = cmd_quote(command) if self.become else command
        return run_command(self.core_ci.args,
                           ['ssh', '-tt', '-q'] + self.ssh_args +
                           options +
                           ['-p', str(self.core_ci.connection.port),
                            '%s@%s' % (self.core_ci.connection.username, self.core_ci.connection.hostname)] +
                           self.become + [command], capture=capture)

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
