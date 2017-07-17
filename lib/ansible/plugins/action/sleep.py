# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from time import sleep

from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    ''' Sleeps for some time '''

    def run(self, tmp=None, task_vars=dict()):
        ''' Run the sleep action module '''

        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False

        try:
            minutes = int(self._task.args.get('minutes', 0))
            seconds = int(self._task.args.get('seconds', 0))
        except ValueError as e:
            result['elapsed'] = 0
            result['failed'] = True
            result['msg'] = u"non-integer value given for 'minutes' or 'seconds':\n%s" % to_text(e)
            return result

        duration = minutes * 60 + seconds
        if duration <= 0:
            duration = 1

        sleep(duration)

        result['elapsed'] = duration

        return result
