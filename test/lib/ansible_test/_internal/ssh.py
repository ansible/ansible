"""High level functions for working with SSH."""

from __future__ import annotations

import dataclasses
import itertools
import json
import os
import pathlib
import random
import re
import subprocess
import shlex
import shutil
import sys
import tempfile
import time
import types
import typing as t

from .encoding import (
    to_text,
)

from .host_configs import (
    NativePythonConfig,
)

from .util import (
    ApplicationError,
    ANSIBLE_TEST_DATA_ROOT,
    common_environment,
    display,
    exclude_none_values,
    sanitize_host_name,
)

from .util_common import (
    get_python_injector_env,
)

from .config import (
    CommonConfig,
    EnvironmentConfig,
)

PORT_FORWARD_RE = re.compile(r'^Allocated port (?P<src_port>[0-9]+) for remote forward to (?P<dst_host>[^:]+):(?P<dst_port>[0-9]+)$')


@dataclasses.dataclass
class SshConnectionDetail:
    """Information needed to establish an SSH connection to a host."""

    name: str
    host: str
    port: t.Optional[int]
    user: str
    identity_file: str
    python_interpreter: t.Optional[str] = None
    powershell_interpreter: str | None = None
    shell_type: t.Optional[str] = None
    enable_rsa_sha1: bool = False

    def __post_init__(self):
        self.name = sanitize_host_name(self.name)

    @property
    def options(self) -> dict[str, str]:
        """OpenSSH config options, which can be passed to the `ssh` CLI with the `-o` argument."""
        options: dict[str, str] = {}

        if self.enable_rsa_sha1:
            # Newer OpenSSH clients connecting to older SSH servers must explicitly enable ssh-rsa support.
            # OpenSSH 8.8, released on 2021-09-26, deprecated using RSA with the SHA-1 hash algorithm (ssh-rsa).
            # OpenSSH 7.2, released on 2016-02-29, added support for using RSA with SHA-256/512 hash algorithms.
            # See: https://www.openssh.com/txt/release-8.8
            algorithms = '+ssh-rsa'  # append the algorithm to the default list, requires OpenSSH 7.0 or later

            options.update(
                # Host key signature algorithms that the client wants to use.
                # Available options can be found with `ssh -Q HostKeyAlgorithms` or `ssh -Q key` on older clients.
                # This option was updated in OpenSSH 7.0, released on 2015-08-11, to support the "+" prefix.
                # See: https://www.openssh.com/txt/release-7.0
                HostKeyAlgorithms=algorithms,
                # Signature algorithms that will be used for public key authentication.
                # Available options can be found with `ssh -Q PubkeyAcceptedAlgorithms` or `ssh -Q key` on older clients.
                # This option was added in OpenSSH 7.0, released on 2015-08-11.
                # See: https://www.openssh.com/txt/release-7.0
                # This option is an alias for PubkeyAcceptedAlgorithms, which was added in OpenSSH 8.5.
                # See: https://www.openssh.com/txt/release-8.5
                PubkeyAcceptedKeyTypes=algorithms,
            )

        return options


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
        if self.pending_forwards:
            self.forwards = _collect_port_forwards(self._process.stderr if self._process else None, self.pending_forwards)
            self.pending_forwards = []

        return self.forwards


@dataclasses.dataclass(frozen=True, kw_only=True)
class AnsibleSshForwarderHostInfo:
    """Information about the remote host that Ansible is connecting to for SSH port forwarding."""

    inventory_hostname: str
    hostname: str
    is_localhost: bool = False


class AnsibleSshForwarder:
    """Wrapper around ansible-playbook process that is forwarding ports over SSH."""

    def __init__(
        self,
        process: subprocess.Popen | None,
        forwards: list[tuple[str, int]],
        temp_dir: pathlib.Path,
        stdout: pathlib.Path,
        ssh_log_path: pathlib.Path,
        host_facts_path: pathlib.Path,
    ) -> None:
        self._process = process
        self._pending_forwards = forwards
        self._temp_dir = temp_dir
        self._stdout = stdout
        self._ssh_log_path = ssh_log_path
        self._host_facts_path = host_facts_path

        self._forwards: dict[tuple[str, int], int] | None = None
        self._host_info: AnsibleSshForwarderHostInfo | None = None

    @classmethod
    def create(
        cls,
        args: CommonConfig,
        forwards: list[tuple[str, int]],
        *,
        inventory: str | None = None,
        host_limit: str | None = None,
    ) -> AnsibleSshForwarder:
        """Create a new AnsibleSshForwarder instance, starting the ansible-playbook process that will set up the SSH port forwards."""
        if isinstance(args, EnvironmentConfig):
            python = args.controller_python
        else:
            python = NativePythonConfig()
            python.version = '.'.join(str(v) for v in sys.version_info[:2])
            python.path = sys.executable

        ansible_env = os.environ.copy()
        ansible_env |= dict(
            ANSIBLE_DEVEL_WARNING='false',
            ANSIBLE_DISPLAY_TRACEBACK=args.display_traceback,
            ANSIBLE_FORCE_COLOR='false',
            ANSIBLE_INVENTORY_UNPARSED_FAILED='false',
            ANSIBLE_LOG_VERBOSITY=str(args.verbosity),
            ANSIBLE_NOCOLOR='true',
        )

        temp_dir = pathlib.Path(tempfile.mkdtemp())
        try:
            # To avoid a deadlock if the Ansible process writes too much to
            # stdout/stderr we redirect it to a temporary file.
            ansible_stdout = temp_dir / 'ansible_stdout.log'

            # Stores the ssh port forwarding information that the playbook uses
            # to capture the dynamically allocated ports.
            ssh_log_path = temp_dir / 'ssh_debug.log'
            resolve_ssh_log_path = str(ssh_log_path.resolve())

            # Stores the host facts and processed forwards ports generated by
            # the playbook.
            host_facts_path = temp_dir / 'host_facts.json'

            ssh_args = [
                '-C',
                '-E',
                resolve_ssh_log_path,
            ]
            for forward_host, forward_port in forwards:
                bind_port = 0  # request SSH to automatically assign a port on the remote side
                ssh_args.extend(['-R', f'{bind_port}:{forward_host}:{forward_port}'])

            playbook_path = pathlib.Path(ANSIBLE_TEST_DATA_ROOT) / 'playbooks' / 'debug_port_forwarder.yml'
            playbook_extra_args = dict(
                ansible_ssh_args=shlex.join(ssh_args),
                _ansible_test_debugger_ssh_log_path=resolve_ssh_log_path,
                _ansible_test_debugger_host_info_path=str(host_facts_path.resolve()),
            )

            playbook_cmd = [
                'ansible-playbook',
                str(playbook_path.resolve()),
                '--extra-vars',
                json.dumps(playbook_extra_args),
            ]
            if inventory:
                playbook_cmd.extend(['--inventory', inventory])
            if host_limit:
                playbook_cmd.extend(['--limit', host_limit])

            if args.explain:
                proc = None
            else:
                with open(ansible_stdout, 'w') as stdout:
                    proc = subprocess.Popen(  # pylint: disable=consider-using-with  # AnsibleSshForwarder manages lifetime.
                        playbook_cmd,
                        stdout=stdout,
                        stderr=subprocess.STDOUT,
                        stdin=subprocess.DEVNULL,
                        env=get_python_injector_env(python, ansible_env),
                    )

            return AnsibleSshForwarder(
                process=proc,
                forwards=forwards,
                temp_dir=temp_dir,
                stdout=ansible_stdout,
                ssh_log_path=ssh_log_path,
                host_facts_path=host_facts_path,
            )

        except Exception:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def __enter__(self) -> AnsibleSshForwarder:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self._terminate_process()
        shutil.rmtree(self._temp_dir, ignore_errors=True)
        return

    def collect_port_forwards(self, timeout: int | None = None) -> dict[tuple[str, int], int]:
        """Collect port assignments for dynamic SSH port forwards."""
        if self._forwards is None:
            # As the reader is a file we cannot rely on it to block a read when
            # waiting for output. Instead we provide a callback that checks if
            # the process is still running and adds a simple sleep to avoid
            # busy looping.
            def is_alive() -> bool:
                if self._process and self._process.poll() is None:
                    time.sleep(1)
                    return True

                return False

            try:
                with open(self._ssh_log_path, 'r') as log_file:
                    self._forwards = _collect_port_forwards(
                        reader=log_file if self._process else None,
                        pending_forwards=self._pending_forwards,
                        ignore_unexpected_output=True,
                        timeout=timeout,
                        alive_check=is_alive,
                    )

            except (ApplicationError, TimeoutError) as e:
                rc = self._terminate_process()
                stdout = self._stdout.read_text()
                msg = f'Failed to retrieve SSH port forwards. Ansible process exited with code {rc}. Ansible playbook output:\n{stdout}'
                raise ApplicationError(msg) from e

        return self._forwards

    def get_host_info(self, timeout: int | None = None) -> AnsibleSshForwarderHostInfo:
        """Get information about the remote host that Ansible is connecting to for SSH port forwarding."""
        if self._host_info is not None:
            return self._host_info

        if self._process is None:  # explain mode
            self._host_info = AnsibleSshForwarderHostInfo(
                inventory_hostname='explain-mode',
                hostname='explain-mode',
                is_localhost=True,
            )
            return self._host_info

        start_time = time.time()
        while not self._host_facts_path.exists():
            if self._process.poll() is not None:
                rc = self._terminate_process()
                stdout = self._stdout.read_text()

                if stdout.find("no hosts matched") != -1:
                    # We fallback to localhost when:
                    # no inventory was provided or inventory had no hosts
                    # a single host running with the local connection was used
                    self._host_info = AnsibleSshForwarderHostInfo(
                        inventory_hostname='localhost',
                        hostname='localhost',
                        is_localhost=True,
                    )
                    return self._host_info

                msg = f"Ansible port forwarding playbook process exited before host facts were collected. " \
                    f"Ansible process exited with code {rc}. Ansible playbook output:\n{stdout}"
                raise ApplicationError(msg)

            if timeout is not None and time.time() - start_time > timeout:
                rc = self._terminate_process()
                stdout = self._stdout.read_text()
                msg = f"Failed to retrieve debugger host info within the specified timeout of {timeout} seconds. " \
                    f"Ansible process exited with code {rc}. Ansible playbook output:\n{stdout}"
                raise TimeoutError(msg)

            time.sleep(1)

        raw_host_info = self._host_facts_path.read_text()
        try:
            host_info = json.loads(raw_host_info)
        except json.JSONDecodeError as e:
            rc = self._terminate_process()
            stdout = self._stdout.read_text()
            msg = f"Failed to parse debugger host info JSON. Ansible process exited with code {rc}. " \
                f"Ansible playbook output:\n{stdout}\n" \
                f"Raw host info content:\n{raw_host_info}"
            raise ApplicationError(msg) from e

        self._host_info = AnsibleSshForwarderHostInfo(
            inventory_hostname=host_info.get('inventory_hostname', 'Unknown inventory hostname'),
            hostname=host_info.get('hostname', 'Unknown hostname'),
        )
        return self._host_info

    def _terminate_process(self) -> int:
        if not self._process:
            return 0  # explain mode

        if self._process.poll() is None:
            self._process.terminate()

        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()

        return self._process.returncode


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
    ]  # fmt: skip

    if not command:
        cmd.append('-N')  # do not execute a remote command

    if ssh.port:
        cmd.extend(['-p', str(ssh.port)])  # port to connect to on the remote host

    if ssh.user:
        cmd.extend(['-l', ssh.user])  # user to log in as on the remote machine

    ssh_options: dict[str, t.Union[int, str]] = dict(
        BatchMode='yes',
        ExitOnForwardFailure='yes',
        LogLevel='ERROR',
        ServerAliveCountMax=4,
        ServerAliveInterval=15,
        StrictHostKeyChecking='no',
        UserKnownHostsFile='/dev/null',
    )

    ssh_options.update(options or {})

    cmd.extend(ssh_options_to_list(ssh_options))
    cmd.extend(cli_args or [])
    cmd.append(ssh.host)

    if command:
        cmd.append(command)

    return cmd


def ssh_options_to_list(options: t.Union[dict[str, t.Union[int, str]], dict[str, str]]) -> list[str]:
    """Format a dictionary of SSH options as a list suitable for passing to the `ssh` command."""
    return list(itertools.chain.from_iterable(
        ('-o', f'{key}={value}') for key, value in sorted(options.items())
    ))


def ssh_options_to_str(options: t.Union[dict[str, t.Union[int, str]], dict[str, str]]) -> str:
    """Format a dictionary of SSH options as a string suitable for passing as `ansible_ssh_extra_args` in inventory."""
    return shlex.join(ssh_options_to_list(options))


def run_ssh_command(
    args: CommonConfig,
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

    if args.explain:
        process = SshProcess(None)
    else:
        process = SshProcess(subprocess.Popen(cmd, env=env, bufsize=-1,  # pylint: disable=consider-using-with
                                              stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE))

    return process


def create_ssh_port_forwards(
    args: CommonConfig,
    ssh: SshConnectionDetail,
    forwards: list[tuple[str, int]],
) -> SshProcess:
    """
    Create SSH port forwards using the provided list of tuples (target_host, target_port).
    Port bindings will be automatically assigned by SSH and must be collected with a subsequent call to collect_port_forwards.
    """
    options: dict[str, t.Union[str, int]] = dict(
        LogLevel='INFO',  # info level required to get messages on stderr indicating the ports assigned to each forward
        ControlPath='none',  # if the user has ControlPath set up for every host, it will prevent creation of forwards
    )

    cli_args = []

    for forward_host, forward_port in forwards:
        cli_args.extend(['-R', ':'.join([str(0), forward_host, str(forward_port)])])

    process = run_ssh_command(args, ssh, options, cli_args)
    process.pending_forwards = forwards

    return process


def create_ssh_port_redirects(
    args: CommonConfig,
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
                ansible_pwsh_interpreter=ssh.powershell_interpreter,
                ansible_shell_type=ssh.shell_type,
                ansible_ssh_extra_args=ssh_options_to_str(dict(UserKnownHostsFile='/dev/null', **ssh.options)),  # avoid changing the test environment
                ansible_ssh_host_key_checking='no',
            ))) for ssh in ssh_connections),
        ),
    )

    inventory_text = json.dumps(inventory, indent=4, sort_keys=True)

    display.info('>>> SSH Inventory\n%s' % inventory_text, verbosity=3)

    return inventory_text


def _collect_port_forwards(
    reader: t.IO | None,
    pending_forwards: list[tuple[str, int]],
    ignore_unexpected_output: bool = False,
    alive_check: t.Callable[[], bool] | None = None,
    timeout: int | None = None,
) -> dict[tuple[str, int], int]:
    """Collect port assignments for dynamic SSH port forwards from the provided reader."""
    errors: list[str] = []

    display.info('Collecting %d SSH port forward(s).' % len(pending_forwards), verbosity=2)

    start_time = time.time()
    forwards = {}
    pending = pending_forwards.copy()
    while pending:
        if timeout is not None and time.time() - start_time > timeout:
            raise TimeoutError('Timed out while waiting for SSH port forwards to be established.')

        if reader:
            line_bytes = reader.readline()

            if not line_bytes:
                if alive_check and alive_check():
                    continue  # process is still alive, keep waiting for output

                if errors:
                    details = ':\n%s' % '\n'.join(errors)
                else:
                    details = '.'

                raise ApplicationError('SSH port forwarding failed%s' % details)

            line = to_text(line_bytes).strip()

            match = re.search(r'^Allocated port (?P<src_port>[0-9]+) for remote forward to (?P<dst_host>[^:]+):(?P<dst_port>[0-9]+)$', line)

            if match:
                src_port = int(match.group('src_port'))
                dst_host = str(match.group('dst_host'))
                dst_port = int(match.group('dst_port'))

                dst = (dst_host, dst_port)

            elif ignore_unexpected_output or re.search(r'^Warning: Permanently added .* to the list of known hosts\.$', line):
                continue

            else:
                display.warning('Unexpected SSH port forwarding output: %s' % line, verbosity=2)

                errors.append(line)
                continue
        else:
            # explain mode
            dst = pending[0]
            src_port = random.randint(40000, 50000)

        pending.remove(dst)
        forwards[dst] = src_port

    display.info('Collected %d SSH port forward(s):\n%s' % (
        len(forwards), '\n'.join('%s -> %s:%s' % (src_port, dst[0], dst[1]) for dst, src_port in sorted(forwards.items()))), verbosity=2)

    return forwards
