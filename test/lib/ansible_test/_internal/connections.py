"""Connection abstraction for interacting with test hosts."""
from __future__ import annotations

import abc
import shlex
import sys
import tempfile
import typing as t

from .io import (
    read_text_file,
)

from .config import (
    EnvironmentConfig,
)

from .util import (
    Display,
    SubprocessError,
    retry,
)

from .util_common import (
    run_command,
)

from .docker_util import (
    DockerInspect,
    docker_exec,
    docker_inspect,
    docker_network_disconnect,
)

from .ssh import (
    SshConnectionDetail,
)

from .become import (
    Become,
)


class Connection(metaclass=abc.ABCMeta):
    """Base class for connecting to a host."""
    @abc.abstractmethod
    def run(self,
            command,  # type: t.List[str]
            capture=False,  # type: bool
            data=None,  # type: t.Optional[str]
            stdin=None,  # type: t.Optional[t.IO[bytes]]
            stdout=None,  # type: t.Optional[t.IO[bytes]]
            ):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
        """Run the specified command and return the result."""

    def extract_archive(self,
                        chdir,  # type: str
                        src,  # type: t.IO[bytes]
                        ):
        """Extract the given archive file stream in the specified directory."""
        # This will not work on AIX.
        # However, AIX isn't supported as a controller, which is where this would be needed.
        tar_cmd = ['tar', 'oxzf', '-', '-C', chdir]

        retry(lambda: self.run(tar_cmd, stdin=src))

    def create_archive(self,
                       chdir,  # type: str
                       name,  # type: str
                       dst,  # type: t.IO[bytes]
                       exclude=None,  # type: t.Optional[str]
                       ):
        """Create the specified archive file stream from the specified directory, including the given name and optionally excluding the given name."""
        tar_cmd = ['tar', 'cf', '-', '-C', chdir]
        gzip_cmd = ['gzip']

        if exclude:
            # This will not work on AIX.
            # However, AIX isn't supported as a controller, which is where this would be needed.
            tar_cmd += ['--exclude', exclude]

        tar_cmd.append(name)

        # Using gzip to compress the archive allows this to work on all POSIX systems we support, including AIX.
        commands = [tar_cmd, gzip_cmd]

        sh_cmd = ['sh', '-c', ' | '.join(' '.join(shlex.quote(cmd) for cmd in command) for command in commands)]

        retry(lambda: self.run(sh_cmd, stdout=dst))


class LocalConnection(Connection):
    """Connect to localhost."""
    def __init__(self, args):  # type: (EnvironmentConfig) -> None
        self.args = args

    def run(self,
            command,  # type: t.List[str]
            capture=False,  # type: bool
            data=None,  # type: t.Optional[str]
            stdin=None,  # type: t.Optional[t.IO[bytes]]
            stdout=None,  # type: t.Optional[t.IO[bytes]]
            ):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
        """Run the specified command and return the result."""
        return run_command(
            args=self.args,
            cmd=command,
            capture=capture,
            data=data,
            stdin=stdin,
            stdout=stdout,
        )


class SshConnection(Connection):
    """Connect to a host using SSH."""
    def __init__(self, args, settings, become=None):  # type: (EnvironmentConfig, SshConnectionDetail, t.Optional[Become]) -> None
        self.args = args
        self.settings = settings
        self.become = become

        self.options = ['-i', settings.identity_file]

        ssh_options = dict(
            BatchMode='yes',
            StrictHostKeyChecking='no',
            UserKnownHostsFile='/dev/null',
            ServerAliveInterval=15,
            ServerAliveCountMax=4,
        )

        for ssh_option in sorted(ssh_options):
            self.options.extend(['-o', f'{ssh_option}={ssh_options[ssh_option]}'])

    def run(self,
            command,  # type: t.List[str]
            capture=False,  # type: bool
            data=None,  # type: t.Optional[str]
            stdin=None,  # type: t.Optional[t.IO[bytes]]
            stdout=None,  # type: t.Optional[t.IO[bytes]]
            ):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
        """Run the specified command and return the result."""
        options = list(self.options)

        if self.become:
            command = self.become.prepare_command(command)

        options.append('-q')

        if not data and not stdin and not stdout and sys.stdin.isatty():
            options.append('-tt')

        with tempfile.NamedTemporaryFile(prefix='ansible-test-ssh-debug-', suffix='.log') as ssh_logfile:
            options.extend(['-vvv', '-E', ssh_logfile.name])

            if self.settings.port:
                options.extend(['-p', str(self.settings.port)])

            options.append(f'{self.settings.user}@{self.settings.host}')
            options.append(' '.join(shlex.quote(cmd) for cmd in command))

            def error_callback(ex):  # type: (SubprocessError) -> None
                """Error handler."""
                self.capture_log_details(ssh_logfile.name, ex)

            return run_command(
                args=self.args,
                cmd=['ssh'] + options,
                capture=capture,
                data=data,
                stdin=stdin,
                stdout=stdout,
                error_callback=error_callback,
            )

    @staticmethod
    def capture_log_details(path, ex):  # type: (str, SubprocessError) -> None
        """Read the specified SSH debug log and add relevant details to the provided exception."""
        if ex.status != 255:
            return

        markers = [
            'debug1: Connection Established',
            'debug1: Authentication successful',
            'debug1: Entering interactive session',
            'debug1: Sending command',
            'debug2: PTY allocation request accepted',
            'debug2: exec request accepted',
        ]

        file_contents = read_text_file(path)
        messages = []

        for line in reversed(file_contents.splitlines()):
            messages.append(line)

            if any(line.startswith(marker) for marker in markers):
                break

        message = '\n'.join(reversed(messages))

        ex.message += '>>> SSH Debug Output\n'
        ex.message += '%s%s\n' % (message.strip(), Display.clear)


class DockerConnection(Connection):
    """Connect to a host using Docker."""
    def __init__(self, args, container_id, user=None):  # type: (EnvironmentConfig, str, t.Optional[str]) -> None
        self.args = args
        self.container_id = container_id
        self.user = user  # type: t.Optional[str]

    def run(self,
            command,  # type: t.List[str]
            capture=False,  # type: bool
            data=None,  # type: t.Optional[str]
            stdin=None,  # type: t.Optional[t.IO[bytes]]
            stdout=None,  # type: t.Optional[t.IO[bytes]]
            ):  # type: (...) -> t.Tuple[t.Optional[str], t.Optional[str]]
        """Run the specified command and return the result."""
        options = []

        if self.user:
            options.extend(['--user', self.user])

        if not data and not stdin and not stdout and sys.stdin.isatty():
            options.append('-it')

        return docker_exec(
            args=self.args,
            container_id=self.container_id,
            cmd=command,
            options=options,
            capture=capture,
            data=data,
            stdin=stdin,
            stdout=stdout,
        )

    def inspect(self):  # type: () -> DockerInspect
        """Inspect the container and return a DockerInspect instance with the results."""
        return docker_inspect(self.args, self.container_id)

    def disconnect_network(self, network):  # type: (str) -> None
        """Disconnect the container from the specified network."""
        docker_network_disconnect(self.args, self.container_id, network)
