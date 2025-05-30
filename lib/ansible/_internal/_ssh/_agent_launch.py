from __future__ import annotations

import atexit
import os
import subprocess

from ansible import constants as C
from ansible._internal._errors import _alarm_timeout
from ansible._internal._ssh._ssh_agent import SshAgentClient
from ansible.cli import display
from ansible.errors import AnsibleError
from ansible.module_utils.common.process import get_bin_path

_SSH_AGENT_STDOUT_READ_TIMEOUT = 5  # seconds


def launch_ssh_agent() -> None:
    """If configured via `SSH_AGENT`, launch an ssh-agent for Ansible's use and/or verify access to an existing one."""
    try:
        _launch_ssh_agent()
    except Exception as ex:
        raise AnsibleError("Failed to launch ssh agent.") from ex


def _launch_ssh_agent() -> None:
    ssh_agent_cfg = C.config.get_config_value('SSH_AGENT')

    match ssh_agent_cfg:
        case 'none':
            display.debug('SSH_AGENT set to none')
            return
        case 'auto':
            try:
                ssh_agent_bin = get_bin_path(C.config.get_config_value('SSH_AGENT_EXECUTABLE'))
            except ValueError as e:
                raise AnsibleError('SSH_AGENT set to auto, but cannot find ssh-agent binary.') from e

            ssh_agent_dir = os.path.join(C.DEFAULT_LOCAL_TMP, 'ssh_agent')
            os.mkdir(ssh_agent_dir, 0o700)
            sock = os.path.join(ssh_agent_dir, 'agent.sock')
            display.vvv('SSH_AGENT: starting...')

            try:
                p = subprocess.Popen(
                    [ssh_agent_bin, '-D', '-s', '-a', sock],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except OSError as e:
                raise AnsibleError('Could not start ssh-agent.') from e

            atexit.register(p.terminate)

            help_text = f'The ssh-agent {ssh_agent_bin!r} might be an incompatible agent.'
            expected_stdout = 'SSH_AUTH_SOCK'

            try:
                with _alarm_timeout.AnsibleTimeoutError.alarm_timeout(_SSH_AGENT_STDOUT_READ_TIMEOUT):
                    stdout = p.stdout.read(len(expected_stdout))
            except _alarm_timeout.AnsibleTimeoutError as e:
                display.error_as_warning(
                    msg=f'Timed out waiting for expected stdout {expected_stdout!r} from ssh-agent.',
                    exception=e,
                    help_text=help_text,
                )
            else:
                if stdout != expected_stdout:
                    display.warning(
                        msg=f'The ssh-agent output {stdout!r} did not match expected {expected_stdout!r}.',
                        help_text=help_text,
                    )

            if p.poll() is not None:
                raise AnsibleError(
                    message='The ssh-agent terminated prematurely.',
                    help_text=f'{help_text}\n\nReturn Code: {p.returncode}\nStandard Error:\n{p.stderr.read()}',
                )

            display.vvv(f'SSH_AGENT: ssh-agent[{p.pid}] started and bound to {sock}')
        case _:
            sock = ssh_agent_cfg

    try:
        with SshAgentClient(sock) as client:
            client.list()
    except Exception as e:
        raise AnsibleError(f'Could not communicate with ssh-agent using auth sock {sock!r}.') from e

    os.environ['SSH_AUTH_SOCK'] = os.environ['ANSIBLE_SSH_AGENT'] = sock
