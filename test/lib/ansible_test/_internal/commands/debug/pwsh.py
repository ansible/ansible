"""Opens an interactive shell or runs a command for debugging PowerShell modules."""

from __future__ import annotations

import dataclasses
import json
import os
import socket

from ...util import (
    ApplicationError,
)

from ...util_common import (
    run_command,
)

from ...config import (
    PwshDebugConfig,
)
from ...ssh import (
    create_ansible_ssh_port_forwards,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class PwshDebugConfigV1:
    version: int
    host: str
    port: int
    token: str

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PwshDebugConfigV1:
        version = data.get('version', None)
        if version != 1:
            raise ApplicationError(
                f'Unsupported PowerShell listener configuration version: {version}. Check that the Ansible.Debugger '
                'PowerShell module running is compatible with this version of ansible-test.')

        host = data.get('host', 'localhost')
        port = int(data.get('port', 0))
        if not port:
            raise ApplicationError(f"Invalid PowerShell listener configuration, no 'port' specified.")

        token = str(data.get('token', None))
        if not token:
            raise ApplicationError(f"Invalid PowerShell listener configuration, no 'token' specified.")

        return cls(
            version=version,
            host=host,
            port=port,
            token=token,
        )


def command_pwsh_debug(args: PwshDebugConfig) -> None:
    """Entry point for the `pwsh-debug` command."""
    listener_path = os.path.expanduser('~/.ansible/test/debugging/pwsh-listener.sock')

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as debug_sock:
        try:
            debug_sock.connect(listener_path)
        except FileNotFoundError as e:
            raise ApplicationError(
                "PowerShell debug listener is not running. Ensure that the Start-AnsibleDebugger cmdlet from the "
                "Ansible.Debugger PowerShell module is running.") from e

        debug_config = _read_debug_config(debug_sock)

        # We forward the local ports to the remote host through an Ansible playbook.
        # This allows Ansible to handle the SSH connection and host selection
        # based on the user provided inventory.
        with create_ansible_ssh_port_forwards(
            args,
            [(debug_config.host, debug_config.port)],
            inventory=args.inventory,
            host_limit=args.limit,
        ) as ansible_proc:
            forwarded_port = list(ansible_proc.collect_port_forwards(timeout=30).values())[0]

            env = os.environ.copy()

            pwsh_config = dict(
                wait=args.wait_at_entry,
                host='localhost',
                port=forwarded_port,
                token=debug_config.token,
            )
            env['_ANSIBLE_ANSIBALLZ_PWSH_DEBUGGER_CONFIG'] = json.dumps(pwsh_config)

            if args.cmd:
                cmd = args.cmd
            else:
                shell = os.environ.get('SHELL', 'bash')
                cmd = [shell, '-i']

            run_command(
                args,
                cmd,
                capture=False,
                interactive=True,
                env=env,
            )


def _read_debug_config(sock: socket.socket) -> PwshDebugConfigV1:
    """Reads the debug configuration from the Ansible.Debugger socket."""
    buffer = bytearray(256)
    buffer_view = memoryview(buffer)
    read = 0
    while read < 4:
        read += sock.recv_into(buffer_view[read:])

    total_length = int.from_bytes(buffer_view[:4], byteorder='little') + 4

    # Increase the buffer size if the total length is larger than the initial buffer
    if len(buffer) < total_length:
        del buffer_view
        buffer.extend(bytearray(total_length - len(buffer)))
        buffer_view = memoryview(buffer)

    while read < total_length:
        read += sock.recv_into(buffer_view[read:])

    config = json.loads(buffer_view[4:total_length].tobytes().decode("utf-8"))
    return PwshDebugConfigV1.from_dict(config)
