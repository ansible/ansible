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
import sys
import time

from termios import tcflush, TCIFLUSH

from ansible.errors import *
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    ''' pauses execution for a length or time, or until input is received '''

    PAUSE_TYPES = ['seconds', 'minutes', 'prompt', '']
    BYPASS_HOST_LOOP = True

    def run(self, tmp=None, task_vars=dict()):
        ''' run the pause action module '''

        duration_unit = 'minutes'
        prompt = None
        seconds = None
        result = dict(
            changed = False,
            rc      = 0,
            stderr  = '',
            stdout  = '',
            start   = None,
            stop    = None,
            delta   = None,
        )

        # FIXME: not sure if we can get this info directly like this anymore?
        #hosts = ', '.join(self.runner.host_set)

        # Is 'args' empty, then this is the default prompted pause
        if self._task.args is None or len(self._task.args.keys()) == 0:
            pause_type = 'prompt'
            #prompt = "[%s]\nPress enter to continue:\n" % hosts
            prompt = "[%s]\nPress enter to continue:\n" % self._task.get_name().strip()

        # Are 'minutes' or 'seconds' keys that exist in 'args'?
        elif 'minutes' in self._task.args or 'seconds' in self._task.args:
            try:
                if 'minutes' in self._task.args:
                    pause_type = 'minutes'
                    # The time() command operates in seconds so we need to
                    # recalculate for minutes=X values.
                    seconds = int(self._task.args['minutes']) * 60
                else:
                    pause_type = 'seconds'
                    seconds = int(self._task.args['seconds'])
                    duration_unit = 'seconds'

            except ValueError as e:
                return dict(failed=True, msg="non-integer value given for prompt duration:\n%s" % str(e))

        # Is 'prompt' a key in 'args'?
        elif 'prompt' in self._task.args:
            pause_type = 'prompt'
            #prompt = "[%s]\n%s:\n" % (hosts, self._task.args['prompt'])
            prompt = "[%s]\n%s:\n" % (self._task.get_name().strip(), self._task.args['prompt'])

        # I have no idea what you're trying to do. But it's so wrong.
        else:
            return dict(failed=True, msg="invalid pause type given. must be one of: %s" % ", ".join(self.PAUSE_TYPES))

        #vv("created 'pause' ActionModule: pause_type=%s, duration_unit=%s, calculated_seconds=%s, prompt=%s" % \
        #        (self.pause_type, self.duration_unit, self.seconds, self.prompt))

        ########################################################################
        # Begin the hard work!

        start = time.time()
        result['start'] = str(datetime.datetime.now())


        # FIXME: this is all very broken right now, as prompting from the worker side
        #        is not really going to be supported, and actions marked as BYPASS_HOST_LOOP
        #        probably should not be run through the executor engine at all. Also, ctrl+c
        #        is now captured on the parent thread, so it can't be caught here via the
        #        KeyboardInterrupt exception.

        try:
            if not pause_type == 'prompt':
                print("(^C-c = continue early, ^C-a = abort)")
                #print("[%s]\nPausing for %s seconds" % (hosts, seconds))
                print("[%s]\nPausing for %s seconds" % (self._task.get_name().strip(), seconds))
                time.sleep(seconds)
            else:
                # Clear out any unflushed buffered input which would
                # otherwise be consumed by raw_input() prematurely.
                #tcflush(sys.stdin, TCIFLUSH)
                result['user_input'] = raw_input(prompt.encode(sys.stdout.encoding))
        except KeyboardInterrupt:
            while True:
                print('\nAction? (a)bort/(c)ontinue: ')
                c = getch()
                if c == 'c':
                    # continue playbook evaluation
                    break
                elif c == 'a':
                    # abort further playbook evaluation
                    raise ae('user requested abort!')
        finally:
            duration = time.time() - start
            result['stop'] = str(datetime.datetime.now())
            result['delta'] = int(duration)

            if duration_unit == 'minutes':
                duration = round(duration / 60.0, 2)
            else:
                duration = round(duration, 2)

            result['stdout'] = "Paused for %s %s" % (duration, duration_unit)

        return result

