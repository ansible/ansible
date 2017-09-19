# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.parsing.dataloader import DataLoader


class TaskResult:
    '''
    This class is responsible for interpreting the resulting data
    from an executed task, and provides helper methods for determining
    the result of a given task.
    '''

    def __init__(self, host, task, return_data, task_fields=None):
        self._host = host
        self._task = task

        if isinstance(return_data, dict):
            self._result = return_data.copy()
        else:
            self._result = DataLoader().load(return_data)

        if task_fields is None:
            self._task_fields = dict()
        else:
            self._task_fields = task_fields

    @property
    def task_name(self):
        return self._task_fields.get('name', None) or self._task.get_name()

    def is_changed(self):
        return self._check_key('changed')

    def is_skipped(self):
        # loop results
        if 'results' in self._result:
            results = self._result['results']
            # Loop tasks are only considered skipped if all items were skipped.
            # some squashed results (eg, yum) are not dicts and can't be skipped individually
            if results and all(isinstance(res, dict) and res.get('skipped', False) for res in results):
                return True

        # regular tasks and squashed non-dict results
        return self._result.get('skipped', False)

    def is_failed(self):
        if 'failed_when_result' in self._result or \
           'results' in self._result and True in [True for x in self._result['results'] if 'failed_when_result' in x]:
            return self._check_key('failed_when_result')
        else:
            return self._check_key('failed')

    def is_unreachable(self):
        return self._check_key('unreachable')

    def _check_key(self, key):
        '''get a specific key from the result or its items'''

        if isinstance(self._result, dict) and key in self._result:
            return self._result.get(key, False)
        else:
            flag = False
            for res in self._result.get('results', []):
                if isinstance(res, dict):
                    flag |= res.get(key, False)
            return flag
