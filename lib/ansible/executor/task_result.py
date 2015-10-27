# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.parsing.dataloader import DataLoader

class TaskResult:
    '''
    This class is responsible for interpretting the resulting data
    from an executed task, and provides helper methods for determining
    the result of a given task.
    '''

    def __init__(self, host, task, return_data):
        self._host = host
        self._task = task
        if isinstance(return_data, dict):
            self._result = return_data.copy()
        else:
            self._result = DataLoader().load(return_data)

    def is_changed(self):
        return self._check_key('changed')

    def is_skipped(self):
        if 'results' in self._result and self._task.loop:
            flag = True
            for res in self._result.get('results', []):
                if isinstance(res, dict):
                    flag &= res.get('skipped', False)
            return flag
        else:
            return self._result.get('skipped', False)

    def is_failed(self):
        if 'failed_when_result' in self._result or \
           'results' in self._result and True in [True for x in self._result['results'] if 'failed_when_result' in x]:
            return self._check_key('failed_when_result')
        else:
            return self._check_key('failed') or self._result.get('rc', 0) != 0

    def is_unreachable(self):
        return self._check_key('unreachable')

    def _check_key(self, key):
        if 'results' in self._result and self._task.loop:
            flag = False
            for res in self._result.get('results', []):
                if isinstance(res, dict):
                    flag |= res.get(key, False)
            return flag
        else:
            return self._result.get(key, False)
