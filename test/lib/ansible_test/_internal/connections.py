"""Connection abstraction for interacting with test hosts."""
from __future__ import annotations

import abc
import shlex
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
    OutputStream,
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
            command: list[str],
            capture: bool,
            interactive: bool = False,
            data: t.Optional[str] = None,
            stdin: t.Optional[t.IO[bytes]] = None,
            stdout: t.Optional[t.IO[bytes]] = None,
            output_stream: t.Optional[OutputStream] = None,
            ) -> tuple[t.Optional[str], t.Optional[str]]:
        """Run the specified command and return the result."""

    def extract_archive(self,
                        chdir: str,
                        src: t.IO[bytes],
                        ):
        """Extract the given archive file stream in the specified directory."""
        tar_cmd = ['tar', 'oxzf', '-', '-C', chdir]

        retry(lambda: self.run(tar_cmd, stdin=src, capture=True))

    def create_archive(self,
                       chdir: str,
                       name: str,
                       dst: t.IO[bytes],
                       exclude: t.Optional[str] = None,
                       ):
        """Create the specified archive file stream from the specified directory, including the given name and optionally excluding the given name."""
        tar_cmd = ['tar', 'cf', '-', '-C', chdir]
        gzip_cmd = ['gzip']

        if exclude:
            tar_cmd += ['--exclude', exclude]

        tar_cmd.append(name)

        # Using gzip to compress the archive allows this to work on all POSIX systems we support.
        commands = [tar_cmd, gzip_cmd]

        sh_cmd = ['sh', '-c', ' | '.join(shlex.join(command) for command in commands)]

        retry(lambda: self.run(sh_cmd, stdout=dst, capture=True))


class LocalConnection(Connection):
    """Connect to localhost."""
    def __init__(self, args: EnvironmentConfig) -> None:
        self.args = args

    def run(self,
            command: list[str],
            capture: bool,
            interactive: bool = False,
            data: t.Optional[str] = None,
            stdin: t.Optional[t.IO[bytes]] = None,
            stdout: t.Optional[t.IO[bytes]] = None,
            output_stream: t.Optional[OutputStream] = None,
            ) -> tuple[t.Optional[str], t.Optional[str]]:
        """Run the specified command and return the result."""
        return run_command(
            args=self.args,
            cmd=command,
            capture=capture,
            data=data,
            stdin=stdin,
            stdout=stdout,
            interactive=interactive,
            output_stream=output_stream,
        )


class SshConnection(Connection):
    """Connect to a host using SSH."""
    def __init__(self, args: EnvironmentConfig, settings: SshConnectionDetail, become: t.Optional[Become] = None) -> None:
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
            command: list[str],
            capture: bool,
            interactive: bool = False,
            data: t.Optional[str] = None,
            stdin: t.Optional[t.IO[bytes]] = None,
            stdout: t.Optional[t.IO[bytes]] = None,
            output_stream: t.Optional[OutputStream] = None,
            ) -> tuple[t.Optional[str], t.Optional[str]]:
        """Run the specified command and return the result."""
        options = list(self.options)

        if self.become:
            command = self.become.prepare_command(command)

        options.append('-q')

        if interactive:
            options.append('-tt')

        with tempfile.NamedTemporaryFile(prefix='ansible-test-ssh-debug-', suffix='.log') as ssh_logfile:
            options.extend(['-vvv', '-E', ssh_logfile.name])

            if self.settings.port:
                options.extend(['-p', str(self.settings.port)])

            options.append(f'{self.settings.user}@{self.settings.host}')
            options.append(shlex.join(command))

            def error_callback(ex: SubprocessError) -> None:
                """Error handler."""
                self.capture_log_details(ssh_logfile.name, ex)

            return run_command(
                args=self.args,
                cmd=['ssh'] + options,
                capture=capture,
                data=data,
                stdin=stdin,
                stdout=stdout,
                interactive=interactive,
                output_stream=output_stream,
                error_callback=error_callback,
            )

    @staticmethod
    def capture_log_details(path: str, ex: SubprocessError) -> None:
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
    def __init__(self, args: EnvironmentConfig, container_id: str, user: t.Optional[str] = None) -> None:
        self.args = args
        self.container_id = container_id
        self.user: t.Optional[str] = user

    def run(self,
            command: list[str],
            capture: bool,
            interactive: bool = False,
            data: t.Optional[str] = None,
            stdin: t.Optional[t.IO[bytes]] = None,
            stdout: t.Optional[t.IO[bytes]] = None,
            output_stream: t.Optional[OutputStream] = None,
            ) -> tuple[t.Optional[str], t.Optional[str]]:
        """Run the specified command and return the result."""
        options = []

        if self.user:
            options.extend(['--user', self.user])

        if interactive:
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
            interactive=interactive,
            output_stream=output_stream,
        )

    def inspect(self) -> DockerInspect:
        """Inspect the container and return a DockerInspect instance with the results."""
        return docker_inspect(self.args, self.container_id)

    def disconnect_network(self, network: str) -> None:
        """Disconnect the container from the specified network."""
        docker_network_disconnect(self.args, self.container_id, network)
