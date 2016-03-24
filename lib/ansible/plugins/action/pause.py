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
import termios
import time
import tty

from os import isatty
from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class AnsibleTimeoutExceeded(Exception):
    pass


def timeout_handler(signum, frame):
    raise AnsibleTimeoutExceeded


class ActionModule(ActionBase):
    ''' pauses execution for a length or time, or until input is received '''

    PAUSE_TYPES = ['seconds', 'minutes', 'prompt', '']
    BYPASS_HOST_LOOP = True

    def run(self, tmp=None, task_vars=None):
        ''' run the pause action module '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        duration_unit = 'minutes'
        prompt = None
        seconds = None
        result.update(dict(
            changed = False,
            rc      = 0,
            stderr  = '',
            stdout  = '',
            start   = None,
            stop    = None,
            delta   = None,
        ))

        # Is 'args' empty, then this is the default prompted pause
        if self._task.args is None or len(self._task.args.keys()) == 0:
            prompt = "[%s]\nPress enter to continue:" % self._task.get_name().strip()

        # Are 'minutes' or 'seconds' keys that exist in 'args'?
        elif 'minutes' in self._task.args or 'seconds' in self._task.args:
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
                result['msg'] = "non-integer value given for prompt duration:\n%s" % str(e)
                return result

        # Is 'prompt' a key in 'args'?
        elif 'prompt' in self._task.args:
            prompt = "[%s]\n%s:" % (self._task.get_name().strip(), self._task.args['prompt'])

        else:
            # I have no idea what you're trying to do. But it's so wrong.
            result['failed'] = True
            result['msg'] = "invalid pause type given. must be one of: %s" % ", ".join(self.PAUSE_TYPES)
            return result

        ########################################################################
        # Begin the hard work!

        start = time.time()
        result['start'] = str(datetime.datetime.now())
        result['user_input'] = ''

        fd = None
        old_settings = None
        try:
            if seconds is not None:
                # setup the alarm handler
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                # show the prompt
                display.display("Pausing for %d seconds" % seconds)
                display.display("(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)\r"),
            else:
                display.display(prompt)

            # save the attributes on the existing (duped) stdin so
            # that we can restore them later after we set raw mode
            fd = None
            try:
                fd = self._connection._new_stdin.fileno()
            except ValueError:
                # someone is using a closed file descriptor as stdin
                pass
            if fd is not None:
                if isatty(fd):
                    old_settings = termios.tcgetattr(fd)
                    tty.setraw(fd)

                    # flush the buffer to make sure no previous key presses
                    # are read in below
                    termios.tcflush(self._connection._new_stdin, termios.TCIFLUSH)
            while True:
                try:
                    if fd is not None:
                        key_pressed = self._connection._new_stdin.read(1)
                        if key_pressed == '\x03':
                            raise KeyboardInterrupt

                    if not seconds:
                        if fd is None or not isatty(fd):
                            display.warning("Not waiting from prompt as stdin is not interactive")
                            break
                        # read key presses and act accordingly
                        if key_pressed == '\r':
                            break
                        else:
                            result['user_input'] += key_pressed

                except KeyboardInterrupt:
                    if seconds is not None:
                        signal.alarm(0)
                    display.display("Press 'C' to continue the play or 'A' to abort \r"),
                    if self._c_or_a():
                        break
                    else:
                        raise AnsibleError('user requested abort!')


        except AnsibleTimeoutExceeded:
            # this is the exception we expect when the alarm signal
            # fires, so we simply ignore it to move into the cleanup
            pass
        finally:
            # cleanup and save some information
            # restore the old settings for the duped stdin fd
            if not(None in (fd, old_settings)) and isatty(fd):
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            duration = time.time() - start
            result['stop'] = str(datetime.datetime.now())
            result['delta'] = int(duration)

            if duration_unit == 'minutes':
                duration = round(duration / 60.0, 2)
            else:
                duration = round(duration, 2)
            result['stdout'] = "Paused for %s %s" % (duration, duration_unit)

        return result

    def _c_or_a(self):
        while True:
            key_pressed = self._connection._new_stdin.read(1)
            if key_pressed.lower() == 'a':
                return False
            elif key_pressed.lower() == 'c':
                return True
