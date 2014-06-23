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
from ansible.utils import getch, parse_kv
import ansible.utils.template as template
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

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' run the pause action module '''

        # note: this module does not need to pay attention to the 'check'
        # flag, it always runs

        hosts = ', '.join(self.runner.host_set)
        args = {}
        if complex_args:
            args.update(complex_args)
        # extra template call unneeded?
        args.update(parse_kv(template.template(self.runner.basedir, module_args, inject)))

        # Are 'minutes' or 'seconds' keys that exist in 'args'?
        if 'minutes' in args or 'seconds' in args:
            try:
                if 'minutes' in args:
                    self.pause_type = 'minutes'
                    # The time() command operates in seconds so we need to
                    # recalculate for minutes=X values.
                    self.seconds = int(args['minutes']) * 60
                else:
                    self.pause_type = 'seconds'
                    self.seconds = int(args['seconds'])
                    self.duration_unit = 'seconds'
            except ValueError, e:
                raise ae("non-integer value given for prompt duration:\n%s" % str(e))
        # Is 'prompt' a key in 'args'?
        elif 'prompt' in args:
            self.pause_type = 'prompt'
            self.prompt = "[%s]\n%s:\n" % (hosts, args['prompt'])
        # Is 'args' empty, then this is the default prompted pause
        elif len(args.keys()) == 0:
            self.pause_type = 'prompt'
            self.prompt = "[%s]\nPress enter to continue:\n" % hosts
        # I have no idea what you're trying to do. But it's so wrong.
        else:
            raise ae("invalid pause type given. must be one of: %s" % \
                         ", ".join(self.PAUSE_TYPES))

        vv("created 'pause' ActionModule: pause_type=%s, duration_unit=%s, calculated_seconds=%s, prompt=%s" % \
                (self.pause_type, self.duration_unit, self.seconds, self.prompt))

        ########################################################################
        # Begin the hard work!
        try:
            self._start()
            if not self.pause_type == 'prompt':
                print "[%s]\nPausing for %s seconds" % (hosts, self.seconds)
                time.sleep(self.seconds)
            else:
                # Clear out any unflushed buffered input which would
                # otherwise be consumed by raw_input() prematurely.
                tcflush(sys.stdin, TCIFLUSH)
                self.result['user_input'] = raw_input(self.prompt.encode(sys.stdout.encoding))
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
