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

from ansible.callbacks import vv
from ansible.errors import AnsibleError as ae
from ansible.runner.return_data import ReturnData
from ansible.utils import getch
from termios import tcflush, TCIFLUSH
import datetime
import sys
import time


class ActionModule(object):
    ''' pauses execution for a length or time, or until input is received '''

    PAUSE_TYPES = ['seconds', 'minutes', 'prompt', '']
    BYPASS_HOST_LOOP = True

    def __init__(self, runner):
        self.runner = runner
        # Set defaults
        self.duration_unit = 'minutes'
        self.prompt = None
        self.seconds = None
        self.result = {'changed': False,
                       'rc': 0,
                       'stderr': '',
                       'stdout': '',
                       'start': None,
                       'stop': None,
                       'delta': None,
                       }

    def run(self, conn, tmp, module_name, inject):
        ''' run the pause actionmodule '''
        args = self.runner.module_args
        hosts = ', '.join(map(lambda x: x[1], self.runner.host_set))

        (self.pause_type, sep, pause_params) = args.partition('=')

        if self.pause_type == '':
            self.pause_type = 'prompt'
        elif not self.pause_type in self.PAUSE_TYPES:
            raise ae("invalid parameter for pause, '%s'. must be one of: %s" % \
                         (self.pause_type, ", ".join(self.PAUSE_TYPES)))

        # error checking
        if self.pause_type in ['minutes', 'seconds']:
            try:
                int(pause_params)
            except ValueError:
                raise ae("value given to %s parameter invalid: '%s', must be an integer" % \
                             self.pause_type, pause_params)

        # The time() command operates in seconds so we need to
        # recalculate for minutes=X values.
        if self.pause_type == 'minutes':
            self.seconds = int(pause_params) * 60
        elif self.pause_type == 'seconds':
            self.seconds = int(pause_params)
            self.duration_unit = 'seconds'
        else:
            # if no args are given we pause with a prompt
            if pause_params == '':
                self.prompt = "[%s]\nPress enter to continue: " % hosts
            else:
                self.prompt = "[%s]\n%s: " % (hosts, pause_params)

        vv("created 'pause' ActionModule: pause_type=%s, duration_unit=%s, calculated_seconds=%s, prompt=%s" % \
                (self.pause_type, self.duration_unit, self.seconds, self.prompt))

        try:
            self._start()
            if not self.pause_type == 'prompt':
                print "[%s]\nPausing for %s seconds" % (hosts, self.seconds)
                time.sleep(self.seconds)
            else:
                # Clear out any unflushed buffered input which would
                # otherwise be consumed by raw_input() prematurely.
                tcflush(sys.stdin, TCIFLUSH)
                raw_input(self.prompt)
        except KeyboardInterrupt:
            while True:
                print '\nAction? (a)bort/(c)ontinue: '
                c = getch()
                if c == 'c':
                    # continue playbook evaluation
                    break
                elif c == 'a':
                    # abort further playbook evaluation
                    raise ae('user requested abort!')
        finally:
            self._stop()

        return ReturnData(conn=conn, result=self.result)

    def _start(self):
        ''' mark the time of execution for duration calculations later '''
        self.start = time.time()
        self.result['start'] = str(datetime.datetime.now())
        if not self.pause_type == 'prompt':
            print "(^C-c = continue early, ^C-a = abort)"

    def _stop(self):
        ''' calculate the duration we actually paused for and then
        finish building the task result string '''
        duration = time.time() - self.start
        self.result['stop'] = str(datetime.datetime.now())
        self.result['delta'] = int(duration)

        if self.duration_unit == 'minutes':
            duration = round(duration / 60.0, 2)
        else:
            duration = round(duration, 2)

        self.result['stdout'] = "Paused for %s %s" % (duration, self.duration_unit)
