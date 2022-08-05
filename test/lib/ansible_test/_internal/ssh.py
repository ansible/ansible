"""High level functions for working with SSH."""
from __future__ import annotations

import dataclasses
import json
import os
import random
import re
import subprocess
import shlex
import typing as t

from .encoding import (
    to_bytes,
    to_text,
)

from .util import (
    ApplicationError,
    common_environment,
    display,
    exclude_none_values,
    sanitize_host_name,
)

from .config import (
    EnvironmentConfig,
)


@dataclasses.dataclass
class SshConnectionDetail:
    """Information needed to establish an SSH connection to a host."""
    name: str
    host: str
    port: t.Optional[int]
    user: str
    identity_file: str
    python_interpreter: t.Optional[str] = None
    shell_type: t.Optional[str] = None

    def __post_init__(self):
        self.name = sanitize_host_name(self.name)


class SshProcess:
    """Wrapper around an SSH process."""
    def __init__(self, process: t.Optional[subprocess.Popen]) -> None:
        self._process = process
        self.pending_forwards: t.Optional[list[tuple[str, int]]] = None

        self.forwards: dict[tuple[str, int], int] = {}

    def terminate(self) -> None:
        """Terminate the SSH process."""
        if not self._process:
            return  # explain mode

        # noinspection PyBroadException
        try:
            self._process.terminate()
        except Exception:  # pylint: disable=broad-except
            pass

    def wait(self) -> None:
        """Wait for the SSH process to terminate."""
        if not self._process:
            return  # explain mode

        self._process.wait()

    def collect_port_forwards(self) -> dict[tuple[str, int], int]:
        """Collect port assignments for dynamic SSH port forwards."""
        errors: list[str] = []

        display.info('Collecting %d SSH port forward(s).' % len(self.pending_forwards), verbosity=2)

        while self.pending_forwards:
            if self._process:
                line_bytes = self._process.stderr.readline()

                if not line_bytes:
                    if errors:
                        details = ':\n%s' % '\n'.join(errors)
                    else:
                        details = '.'

                    raise ApplicationError('SSH port forwarding failed%s' % details)

                line = to_text(line_bytes).strip()

                match = re.search(r'^Allocated port (?P<src_port>[0-9]+) for remote forward to (?P<dst_host>[^:]+):(?P<dst_port>[0-9]+)$', line)

                if not match:
                    if re.search(r'^Warning: Permanently added .* to the list of known hosts\.$', line):
                        continue

                    display.warning('Unexpected SSH port forwarding output: %s' % line, verbosity=2)

                    errors.append(line)
                    continue

                src_port = int(match.group('src_port'))
                dst_host = str(match.group('dst_host'))
                dst_port = int(match.group('dst_port'))

                dst = (dst_host, dst_port)
            else:
                # explain mode
                dst = self.pending_forwards[0]
                src_port = random.randint(40000, 50000)

            self.pending_forwards.remove(dst)
            self.forwards[dst] = src_port

        display.info('Collected %d SSH port forward(s):\n%s' % (
            len(self.forwards), '\n'.join('%s -> %s:%s' % (src_port, dst[0], dst[1]) for dst, src_port in sorted(self.forwards.items()))), verbosity=2)

        return self.forwards


def create_ssh_command(
        ssh: SshConnectionDetail,
        options: t.Optional[dict[str, t.Union[str, int]]] = None,
        cli_args: list[str] = None,
        command: t.Optional[str] = None,
) -> list[str]:
    """Create an SSH command using the specified options."""
    cmd = [
        'ssh',
        '-n',  # prevent reading from stdin
        '-i', ssh.identity_file,  # file from which the identity for public key authentication is read
    ]

    if not command:
        cmd.append('-N')  # do not execute a remote command

    if ssh.port:
        cmd.extend(['-p', str(ssh.port)])  # port to connect to on the remote host

    if ssh.user:
        cmd.extend(['-l', ssh.user])  # user to log in as on the remote machine

    ssh_options = dict(
        BatchMode='yes',
        ExitOnForwardFailure='yes',
        LogLevel='ERROR',
        ServerAliveCountMax=4,
        ServerAliveInterval=15,
        StrictHostKeyChecking='no',
        UserKnownHostsFile='/dev/null',
    )

    ssh_options.update(options or {})

    for key, value in sorted(ssh_options.items()):
        cmd.extend(['-o', '='.join([key, str(value)])])

    cmd.extend(cli_args or [])
    cmd.append(ssh.host)

    if command:
        cmd.append(command)

    return cmd


def run_ssh_command(
        args: EnvironmentConfig,
        ssh: SshConnectionDetail,
        options: t.Optional[dict[str, t.Union[str, int]]] = None,
        cli_args: list[str] = None,
        command: t.Optional[str] = None,
) -> SshProcess:
    """Run the specified SSH command, returning the created SshProcess instance created."""
    cmd = create_ssh_command(ssh, options, cli_args, command)
    env = common_environment()

    cmd_show = shlex.join(cmd)
    display.info('Run background command: %s' % cmd_show, verbosity=1, truncate=True)

    cmd_bytes = [to_bytes(arg) for arg in cmd]
    env_bytes = dict((to_bytes(k), to_bytes(v)) for k, v in env.items())

    if args.explain:
        process = SshProcess(None)
    else:
        process = SshProcess(subprocess.Popen(cmd_bytes, env=env_bytes, bufsize=-1,  # pylint: disable=consider-using-with
                                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE))

    return process


def create_ssh_port_forwards(
        args: EnvironmentConfig,
        ssh: SshConnectionDetail,
        forwards: list[tuple[str, int]],
) -> SshProcess:
    """
    Create SSH port forwards using the provided list of tuples (target_host, target_port).
    Port bindings will be automatically assigned by SSH and must be collected with a subsequent call to collect_port_forwards.
    """
    options: dict[str, t.Union[str, int]] = dict(
        LogLevel='INFO',  # info level required to get messages on stderr indicating the ports assigned to each forward
    )

    cli_args = []

    for forward_host, forward_port in forwards:
        cli_args.extend(['-R', ':'.join([str(0), forward_host, str(forward_port)])])

    process = run_ssh_command(args, ssh, options, cli_args)
    process.pending_forwards = forwards

    return process


def create_ssh_port_redirects(
        args: EnvironmentConfig,
        ssh: SshConnectionDetail,
        redirects: list[tuple[int, str, int]],
) -> SshProcess:
    """Create SSH port redirections using the provided list of tuples (bind_port, target_host, target_port)."""
    options: dict[str, t.Union[str, int]] = {}
    cli_args = []

    for bind_port, target_host, target_port in redirects:
        cli_args.extend(['-R', ':'.join([str(bind_port), target_host, str(target_port)])])

    process = run_ssh_command(args, ssh, options, cli_args)

    return process


def generate_ssh_inventory(ssh_connections: list[SshConnectionDetail]) -> str:
    """Return an inventory file in JSON format, created from the provided SSH connection details."""
    inventory = dict(
        all=dict(
            hosts=dict((ssh.name, exclude_none_values(dict(
                ansible_host=ssh.host,
                ansible_port=ssh.port,
                ansible_user=ssh.user,
                ansible_ssh_private_key_file=os.path.abspath(ssh.identity_file),
                ansible_connection='ssh',
                ansible_pipelining='yes',
                ansible_python_interpreter=ssh.python_interpreter,
                ansible_shell_type=ssh.shell_type,
                ansible_ssh_extra_args='-o UserKnownHostsFile=/dev/null',  # avoid changing the test environment
                ansible_ssh_host_key_checking='no',
            ))) for ssh in ssh_connections),
        ),
    )

    inventory_text = json.dumps(inventory, indent=4, sort_keys=True)

    display.info('>>> SSH Inventory\n%s' % inventory_text, verbosity=3)

    return inventory_text
