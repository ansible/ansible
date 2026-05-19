"""Opens an interactive shell or runs a command for debugging PowerShell modules."""

from __future__ import annotations

import contextlib
import dataclasses
import json
import os
import socket
import typing as t

from ...util import (
    ApplicationError,
    display,
)

from ...util_common import (
    run_command,
)

from ...config import (
    PwshDebugConfig,
)
from ...ssh import (
    AnsibleSshForwarder,
)


@dataclasses.dataclass(frozen=True, kw_only=True)
class PwshDebugConfigV1:
    """Ansible.Debugger PowerShell module debug configuration version 1."""
    version: int
    host: str
    port: int
    token: str

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> PwshDebugConfigV1:
        """Builds the config from the raw JSON dictionary value."""
        version = data.get('version', None)
        if version != 1:
            raise ApplicationError(
                f'Unsupported PowerShell listener configuration version: {version}. Check that the Ansible.Debugger '
                'PowerShell module running is compatible with this version of ansible-test.')

        host = data.get('host', 'localhost')
        port = int(data.get('port', 0))
        if not port:
            raise ApplicationError("Invalid PowerShell listener configuration, no 'port' specified.")

        token = str(data.get('token', None))
        if not token:
            raise ApplicationError("Invalid PowerShell listener configuration, no 'token' specified.")

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
        display.info(f"Connecting to PowerShell debug listener at {listener_path}", verbosity=1)
        try:
            debug_sock.connect(listener_path)
        except FileNotFoundError as e:
            raise ApplicationError(
                "PowerShell debug listener is not running. Ensure that the Start-AnsibleDebugger cmdlet from the "
                "Ansible.Debugger PowerShell module is running.") from e

        debug_config = _read_debug_config(debug_sock)

        with contextlib.ExitStack() as exit_stack:
            forwarded_port = debug_config.port
            target_inventory_hostname = 'localhost'
            target_hostname = 'localhost'

            if not args.limit or args.limit != 'localhost':
                # We forward the local ports to the remote host through an Ansible playbook.
                # This allows Ansible to handle the SSH connection and host selection
                # based on the user provided inventory. This is skipped if the
                # user has explicitly limited to localhost since it can already
                # connect to the port locally.
                display.info("Attempting to set up SSH port forwarding to the target host through Ansible", verbosity=1)
                ansible_proc = AnsibleSshForwarder.create(
                    args,
                    [(debug_config.host, debug_config.port)],
                    inventory=args.inventory,
                    host_limit=args.limit,
                )
                exit_stack.push(ansible_proc)

                host_info = ansible_proc.get_host_info(timeout=30)
                if not host_info.is_localhost:
                    forwarded_port = list(ansible_proc.collect_port_forwards(timeout=30).values())[0]
                    target_inventory_hostname = host_info.inventory_hostname
                    target_hostname = host_info.hostname

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
                wait_status = "ENABLED (will break at entry)" if args.wait_at_entry else "DISABLED (run until breakpoint)"
                shell = os.environ.get('SHELL', 'bash')

                # Include a banner to help users see what to do next in the
                # interactive shell. We embed this in the script so that it
                # comes after any ansible-test messages.
                banner = f'''
╔════════════════════════════════════════════════════════════════════════════╗
║            PowerShell Module Interactive Debug Shell                       ║
╚════════════════════════════════════════════════════════════════════════════╝

Ansible Inventory Hostname: {target_inventory_hostname}
Remote Hostname: {target_hostname}

Entrypoint wait: {wait_status}
  NOTE: Wait option only works on PowerShell 7+ targets.
        PowerShell 5.1 will always wait at entry regardless of this setting.

USAGE:
  Run ansible or ansible-playbook commands targeting your PowerShell module or
  PowerShell script. The debugger will attach when the module executes.

EXAMPLES:
  ansible localhost -m win_ping
  ansible win_host -m script -a 'test.ps1'
  ansible-playbook my_playbook.yml

TOGGLE WAIT SETTING (PowerShell 7+ only):

  Enable wait at entry point (break before module code runs):
    export _ANSIBLE_ANSIBALLZ_PWSH_DEBUGGER_CONFIG=$(echo "$_ANSIBLE_ANSIBALLZ_PWSH_DEBUGGER_CONFIG" | jq '.wait = true')

  Disable wait (run until manual breakpoint):
    export _ANSIBLE_ANSIBALLZ_PWSH_DEBUGGER_CONFIG=$(echo "$_ANSIBLE_ANSIBALLZ_PWSH_DEBUGGER_CONFIG" | jq '.wait = false')

WHEN FINISHED:
  Type 'exit' to close this shell, or stop the debug session in VSCode.

TROUBLESHOOTING:
  If terminal is broken after stopping the debugger (no echo, weird wrapping):
    • Close the "Python Debug Console" terminal tab in VSCode and restart
    • Or run: stty sane

════════════════════════════════════════════════════════════════════════════
'''

                # Stopping the Python debug session in VSCode can put the
                # terminal in a funky state. It seems like this state happens
                # after the Python process ends so we instead just try and
                # restore some of the known problematic settings before
                # starting our interactive shell.
                cmd = [
                    shell,
                    '-c',
                    f'''
stty icrnl icanon echo 2>/dev/null
{'' if args.nologo else f'cat << \'EOF\'\n{banner}\nEOF'}
exec "$0" -i
''',
                ]

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

    raw_config = buffer_view[4:total_length].tobytes().decode("utf-8")
    display.info(f"Received PowerShell debug configuration: {raw_config}", verbosity=3)
    config = json.loads(raw_config)
    return PwshDebugConfigV1.from_dict(config)
