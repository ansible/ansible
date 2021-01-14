# Copyright 2012, Tim Bielawa <tbielawa@redhat.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import signal
import sys
import termios
import time
import tty

from os import (
    getpgrp,
    isatty,
    tcgetpgrp,
)
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import PY3
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

try:
    import curses

    # Nest the try except since curses.error is not available if curses did not import
    try:
        curses.setupterm()
        HAS_CURSES = True
    except (curses.error, TypeError):
        HAS_CURSES = False
except ImportError:
    HAS_CURSES = False

if HAS_CURSES:
    MOVE_TO_BOL = curses.tigetstr('cr')
    CLEAR_TO_EOL = curses.tigetstr('el')
else:
    MOVE_TO_BOL = b'\r'
    CLEAR_TO_EOL = b'\x1b[K'


class AnsibleTimeoutExceeded(Exception):
    pass


def timeout_handler(signum, frame):
    raise AnsibleTimeoutExceeded


def clear_line(stdout):
    stdout.write(b'\x1b[%s' % MOVE_TO_BOL)
    stdout.write(b'\x1b[%s' % CLEAR_TO_EOL)


def is_interactive(fd=None):
    if fd is None:
        return False

    if isatty(fd):
        # Compare the current process group to the process group associated
        # with terminal of the given file descriptor to determine if the process
        # is running in the background.
        return getpgrp() == tcgetpgrp(fd)
    else:
        return False


class ActionModule(ActionBase):
    ''' pauses execution for a length or time, or until input is received '''

    BYPASS_HOST_LOOP = True
    _VALID_ARGS = frozenset(('echo', 'minutes', 'prompt', 'seconds'))

    def run(self, tmp=None, task_vars=None):
        ''' run the pause action module '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        duration_unit = 'minutes'
        prompt = None
        seconds = None
        echo = True
        echo_prompt = ''
        result.update(dict(
            changed=False,
            rc=0,
            stderr='',
            stdout='',
            start=None,
            stop=None,
            delta=None,
            echo=echo
        ))

        # Should keystrokes be echoed to stdout?
        if 'echo' in self._task.args:
            try:
                echo = boolean(self._task.args['echo'])
            except TypeError as e:
                result['failed'] = True
                result['msg'] = to_native(e)
                return result

            # Add a note saying the output is hidden if echo is disabled
            if not echo:
                echo_prompt = ' (output is hidden)'

        # Is 'prompt' a key in 'args'?
        if 'prompt' in self._task.args:
            prompt = "[%s]\n%s%s:" % (self._task.get_name().strip(), self._task.args['prompt'], echo_prompt)
        else:
            # If no custom prompt is specified, set a default prompt
            prompt = "[%s]\n%s%s:" % (self._task.get_name().strip(), 'Press enter to continue, Ctrl+C to interrupt', echo_prompt)

        # Are 'minutes' or 'seconds' keys that exist in 'args'?
        if 'minutes' in self._task.args or 'seconds' in self._task.args:
            try:
                if 'minutes' in self._task.args:
                    # The time() command operates in seconds so we need to
                    # recalculate for minutes=X values.
                    seconds = int(self._task.args['minutes']) * 60
                else:
                    seconds = int(self._task.args['seconds'])
                    duration_unit = 'seconds'

            except ValueError as e:
                result['failed'] = True
                result['msg'] = u"non-integer value given for prompt duration:\n%s" % to_text(e)
                return result

        ########################################################################
        # Begin the hard work!

        start = time.time()
        result['start'] = to_text(datetime.datetime.now())
        result['user_input'] = b''

        stdin_fd = None
        old_settings = None
        try:
            if seconds is not None:
                if seconds < 1:
                    seconds = 1

                # setup the alarm handler
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)

                # show the timer and control prompts
                display.display("Pausing for %d seconds%s" % (seconds, echo_prompt))
                display.display("(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)\r"),

                # show the prompt specified in the task
                if 'prompt' in self._task.args:
                    display.display(prompt)

            else:
                display.display(prompt)

            # save the attributes on the existing (duped) stdin so
            # that we can restore them later after we set raw mode
            stdin_fd = None
            stdout_fd = None
            try:
                if PY3:
                    stdin = self._connection._new_stdin.buffer
                    stdout = sys.stdout.buffer
                else:
                    stdin = self._connection._new_stdin
                    stdout = sys.stdout
                stdin_fd = stdin.fileno()
                stdout_fd = stdout.fileno()
            except (ValueError, AttributeError):
                # ValueError: someone is using a closed file descriptor as stdin
                # AttributeError: someone is using a null file descriptor as stdin on windoze
                stdin = None
            interactive = is_interactive(stdin_fd)
            if interactive:
                # grab actual Ctrl+C sequence
                try:
                    intr = termios.tcgetattr(stdin_fd)[6][termios.VINTR]
                except Exception:
                    # unsupported/not present, use default
                    intr = b'\x03'  # value for Ctrl+C

                # get backspace sequences
                try:
                    backspace = termios.tcgetattr(stdin_fd)[6][termios.VERASE]
                except Exception:
                    backspace = [b'\x7f', b'\x08']

                old_settings = termios.tcgetattr(stdin_fd)
                tty.setraw(stdin_fd)

                # Only set stdout to raw mode if it is a TTY. This is needed when redirecting
                # stdout to a file since a file cannot be set to raw mode.
                if isatty(stdout_fd):
                    tty.setraw(stdout_fd)

                # Only echo input if no timeout is specified
                if not seconds and echo:
                    new_settings = termios.tcgetattr(stdin_fd)
                    new_settings[3] = new_settings[3] | termios.ECHO
                    termios.tcsetattr(stdin_fd, termios.TCSANOW, new_settings)

                # flush the buffer to make sure no previous key presses
                # are read in below
                termios.tcflush(stdin, termios.TCIFLUSH)

            while True:
                if not interactive:
                    if seconds is None:
                        display.warning("Not waiting for response to prompt as stdin is not interactive")
                    if seconds is not None:
                        # Give the signal handler enough time to timeout
                        time.sleep(seconds + 1)
                    break

                try:
                    key_pressed = stdin.read(1)

                    if key_pressed == intr:  # value for Ctrl+C
                        clear_line(stdout)
                        raise KeyboardInterrupt

                    # read key presses and act accordingly
                    if key_pressed in (b'\r', b'\n'):
                        clear_line(stdout)
                        break
                    elif key_pressed in backspace:
                        # delete a character if backspace is pressed
                        result['user_input'] = result['user_input'][:-1]
                        clear_line(stdout)
                        if echo:
                            stdout.write(result['user_input'])
                        stdout.flush()
                    else:
                        result['user_input'] += key_pressed

                except KeyboardInterrupt:
                    signal.alarm(0)
                    display.display("Press 'C' to continue the play or 'A' to abort \r"),
                    if self._c_or_a(stdin):
                        clear_line(stdout)
                        break

                    clear_line(stdout)

                    raise AnsibleError('user requested abort!')

        except AnsibleTimeoutExceeded:
            # this is the exception we expect when the alarm signal
            # fires, so we simply ignore it to move into the cleanup
            pass
        finally:
            # cleanup and save some information
            # restore the old settings for the duped stdin stdin_fd
            if not(None in (stdin_fd, old_settings)) and isatty(stdin_fd):
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)

            duration = time.time() - start
            result['stop'] = to_text(datetime.datetime.now())
            result['delta'] = int(duration)

            if duration_unit == 'minutes':
                duration = round(duration / 60.0, 2)
            else:
                duration = round(duration, 2)
            result['stdout'] = "Paused for %s %s" % (duration, duration_unit)

        result['user_input'] = to_text(result['user_input'], errors='surrogate_or_strict')
        return result

    def _c_or_a(self, stdin):
        while True:
            key_pressed = stdin.read(1)
            if key_pressed.lower() == b'a':
                return False
            elif key_pressed.lower() == b'c':
                return True
