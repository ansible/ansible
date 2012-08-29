# (c) 2012, Tim Bielawa <tbielawa@redhat.com>
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

from ansible.errors import AnsibleError as ae
from termios import tcflush, TCIFLUSH
from ansible.callbacks import vv, vvv
import datetime
import time
import sys


class pause(object):
    ''' pauses execution for a length or time, or until input is received '''

    PAUSE_TYPES = ['seconds', 'minutes', 'prompt']

    def __init__(self, host, module_args):
        self.result = {'changed': False, 'rc': 0, 'stderr': ''}
        (self.pause_type, sep, pause_params) = module_args.partition('=')
        if not self.pause_type in pause.PAUSE_TYPES:
            raise ae("invalid parameter for pause, '%s'. must be one of: %s" % \
                         (self.pause_type, ", ".join(pause.PAUSE_TYPES)))

        # Set defaults
        self.duration_unit = 'minutes'
        self.prompt = None
        self.seconds = None

        # The time() command operates in seconds so we need to
        # recalculate for minutes=X values.
        if self.pause_type == 'minutes':
            self.seconds = int(pause_params) * 60
        elif self.pause_type == 'seconds':
            self.seconds = int(pause_params)
            self.duration_unit = 'seconds'
        else:
            if pause_params == '':
                self.prompt = "[%s] Press enter to continue:" % host
            else:
                self.prompt = "[%s] %s" % (host, pause_params)

        vvv("created Pause() with pause_type=%s, duration_unit=%s, calculated_seconds=%s, prompt=%s" % \
                (self.pause_type, self.duration_unit, self.seconds, self.prompt))

    def _start(self):
        ''' mark the time of execution for duration calculations later '''
        self.start = time.time()
        self.result['start'] = str(datetime.datetime.now())

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

    def run(self):
        ''' kick off the show '''
        try:
            self._start()
            if not self.pause_type == 'prompt':
                print "Pausing for %s %s (^C to continue early)" % (self.seconds, self.duration_unit)
                time.sleep(self.seconds)
            else:
                # Clear out any unflushed buffered input which would
                # otherwise be consumed by raw_input() prematurely.
                tcflush(sys.stdin, TCIFLUSH)
                raw_input(self.prompt)
        except KeyboardInterrupt:
            vv('caught ^C signal')
        finally:
            self._stop()

        return self.result
