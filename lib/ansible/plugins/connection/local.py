# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2015, 2017 Toshio Kuratomi <tkuratomi@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: local
    short_description: execute on controller
    description:
        - This connection plugin allows ansible to execute tasks on the Ansible 'controller' instead of on a remote host.
    author: ansible (@core)
    version_added: historical
    options:
        become_success_timeout:
            version_added: '2.19'
            type: int
            default: 10
            description:
                - Number of seconds to wait for become to succeed when enabled.
                - The default will be used if the configured value is less than 1.
            vars:
                - name: ansible_local_become_success_timeout
        become_strip_preamble:
            version_added: '2.19'
            type: bool
            default: true
            description:
                - Strip internal become output preceding command execution. Disable for additional diagnostics.
            vars:
                - name: ansible_local_become_strip_preamble
    extends_documentation_fragment:
        - connection_pipelining
    notes:
        - The remote user is ignored, the user with which the ansible CLI was executed is used instead.
"""

import functools
import getpass
import os
import pty
import selectors
import shutil
import subprocess
import time
import typing as t

import ansible.constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleConnectionFailure
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.plugins.connection import ConnectionBase
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath

display = Display()


class Connection(ConnectionBase):
    """ Local based connections """

    transport = 'local'
    has_pipelining = True

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:

        super(Connection, self).__init__(*args, **kwargs)
        self.cwd = None
        try:
            self.default_user = getpass.getuser()
        except KeyError:
            display.vv("Current user (uid=%s) does not seem to exist on this system, leaving user empty." % os.getuid())
            self.default_user = ""

    def _connect(self) -> Connection:
        """ connect to the local host; nothing to do here """

        # Because we haven't made any remote connection we're running as
        # the local user, rather than as whatever is configured in remote_user.
        self._play_context.remote_user = self.default_user

        if not self._connected:
            display.vvv(u"ESTABLISH LOCAL CONNECTION FOR USER: {0}".format(self._play_context.remote_user), host=self._play_context.remote_addr)
            self._connected = True
        return self

    def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        """ run a command on the local host """

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.debug("in local.exec_command()")

        executable = C.DEFAULT_EXECUTABLE.split()[0] if C.DEFAULT_EXECUTABLE else None

        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self._play_context.remote_addr)
        display.debug("opening command with Popen()")

        if isinstance(cmd, (str, bytes)):
            cmd = to_text(cmd)
        else:
            cmd = map(to_text, cmd)

        pty_primary = None
        stdin = subprocess.PIPE
        if sudoable and self.become and self.become.expect_prompt() and not self.get_option('pipelining'):
            # Create a pty if sudoable for privilege escalation that needs it.
            # Falls back to using a standard pipe if this fails, which may
            # cause the command to fail in certain situations where we are escalating
            # privileges or the command otherwise needs a pty.
            try:
                pty_primary, stdin = pty.openpty()
            except OSError as ex:
                display.debug(f"Unable to open pty: {ex}")

        p = subprocess.Popen(
            cmd,
            shell=isinstance(cmd, (str, bytes)),
            executable=executable,
            cwd=self.cwd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # if we created a pty, we can close the other half of the pty now, otherwise primary is stdin
        if pty_primary is not None:
            os.close(stdin)

        display.debug("done running command with Popen()")

        become_stdout_bytes, become_stderr_bytes = self._ensure_become_success(p, pty_primary, sudoable)

        display.debug("getting output with communicate()")
        stdout, stderr = p.communicate(in_data)
        display.debug("done communicating")

        # preserve output from privilege escalation stage as `bytes`; it may contain actual output (eg `raw`) or error messages
        stdout = become_stdout_bytes + stdout
        stderr = become_stderr_bytes + stderr

        # finally, close the other half of the pty, if it was created
        if pty_primary:
            os.close(pty_primary)

        display.debug("done with local.exec_command()")
        return p.returncode, stdout, stderr

    def _ensure_become_success(self, p: subprocess.Popen, pty_primary: int, sudoable: bool) -> tuple[bytes, bytes]:
        """
        Ensure that become succeeds, returning a tuple containing stdout captured after success and all stderr.
        Returns immediately if `self.become` or `sudoable` are False, or `build_become_command` was not called, without performing any additional checks.
        """
        if not self.become or not sudoable or not self.become._id:  # _id is set by build_become_command, if it was not called, assume no become
            return b'', b''

        start_seconds = time.monotonic()
        become_stdout = bytearray()
        become_stderr = bytearray()
        last_stdout_prompt_offset = 0
        last_stderr_prompt_offset = 0

        # map the buffers to their associated stream for the selector reads
        become_capture = {
            p.stdout: become_stdout,
            p.stderr: become_stderr,
        }

        expect_password_prompt = self.become.expect_prompt()
        sent_password = False

        def become_error_msg(reason: str) -> str:
            error_message = f'{reason} waiting for become success'

            if expect_password_prompt and not sent_password:
                error_message += ' or become password prompt'

            error_message += '.'

            if become_stdout:
                error_message += f'\n>>> Standard Output\n{to_text(bytes(become_stdout))}'

            if become_stderr:
                error_message += f'\n>>> Standard Error\n{to_text(bytes(become_stderr))}'

            return error_message

        os.set_blocking(p.stdout.fileno(), False)
        os.set_blocking(p.stderr.fileno(), False)

        with selectors.DefaultSelector() as selector:
            selector.register(p.stdout, selectors.EVENT_READ, 'stdout')
            selector.register(p.stderr, selectors.EVENT_READ, 'stderr')

            while not self.become.check_success(become_stdout):
                if not selector.get_map():  # we only reach end of stream after all descriptors are EOF
                    raise AnsibleError(become_error_msg('Premature end of stream'))

                if expect_password_prompt and (
                    self.become.check_password_prompt(become_stdout[last_stdout_prompt_offset:]) or
                    self.become.check_password_prompt(become_stderr[last_stderr_prompt_offset:])
                ):
                    if sent_password:
                        raise AnsibleError(become_error_msg('Duplicate become password prompt encountered'))

                    last_stdout_prompt_offset = len(become_stdout)
                    last_stderr_prompt_offset = len(become_stderr)

                    password_to_send = to_bytes(self.become.get_option('become_pass') or '') + b'\n'

                    if pty_primary is None:
                        p.stdin.write(password_to_send)
                        p.stdin.flush()
                    else:
                        os.write(pty_primary, password_to_send)

                    sent_password = True

                remaining_timeout_seconds = self._become_success_timeout - (time.monotonic() - start_seconds)
                events = selector.select(remaining_timeout_seconds) if remaining_timeout_seconds > 0 else []

                if not events:
                    # ignoring remaining output after timeout to prevent hanging
                    raise AnsibleConnectionFailure(become_error_msg('Timed out'))

                # read all content (non-blocking) from streams that signaled available input and append to the associated buffer
                for key, event in events:
                    obj = t.cast(t.BinaryIO, key.fileobj)

                    if chunk := obj.read():
                        become_capture[obj] += chunk
                    else:
                        selector.unregister(obj)  # EOF on this obj, stop polling it

        os.set_blocking(p.stdout.fileno(), True)
        os.set_blocking(p.stderr.fileno(), True)

        become_stdout_bytes = bytes(become_stdout)
        become_stderr_bytes = bytes(become_stderr)

        if self.get_option('become_strip_preamble'):
            become_stdout_bytes = self.become.strip_become_success(self.become.strip_become_prompt(become_stdout_bytes))
            become_stderr_bytes = self.become.strip_become_prompt(become_stderr_bytes)

        return become_stdout_bytes, become_stderr_bytes

    @functools.cached_property
    def _become_success_timeout(self) -> int:
        """Timeout value for become success in seconds."""
        if (timeout := self.get_option('become_success_timeout')) < 1:
            timeout = C.config.get_config_default('become_success_timeout', plugin_type='connection', plugin_name='local')

        return timeout

    def put_file(self, in_path: str, out_path: str) -> None:
        """ transfer a file from local to local """

        super(Connection, self).put_file(in_path, out_path)

        in_path = unfrackpath(in_path, basedir=self.cwd)
        out_path = unfrackpath(out_path, basedir=self.cwd)

        display.vvv(u"PUT {0} TO {1}".format(in_path, out_path), host=self._play_context.remote_addr)
        if not os.path.exists(to_bytes(in_path, errors='surrogate_or_strict')):
            raise AnsibleFileNotFound("file or module does not exist: {0}".format(to_native(in_path)))
        try:
            shutil.copyfile(to_bytes(in_path, errors='surrogate_or_strict'), to_bytes(out_path, errors='surrogate_or_strict'))
        except shutil.Error:
            raise AnsibleError("failed to copy: {0} and {1} are the same".format(to_native(in_path), to_native(out_path)))
        except OSError as ex:
            raise AnsibleError(f"Failed to transfer file to {out_path!r}.") from ex

    def fetch_file(self, in_path: str, out_path: str) -> None:
        """ fetch a file from local to local -- for compatibility """

        super(Connection, self).fetch_file(in_path, out_path)

        display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path), host=self._play_context.remote_addr)
        self.put_file(in_path, out_path)

    def reset(self) -> None:
        pass

    def close(self) -> None:
        """ terminate the connection; nothing to do here """
        self._connected = False
