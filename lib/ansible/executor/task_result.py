# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible import constants as C
from ansible.parsing.dataloader import DataLoader
from ansible.vars.clean import module_response_deepcopy, strip_internal_keys

_IGNORE = ('failed', 'skipped')
_PRESERVE = ('attempts', 'changed', 'retries')
_SUB_PRESERVE = {'_ansible_delegated_vars': ('ansible_host', 'ansible_port', 'ansible_user', 'ansible_connection')}

# stuff callbacks need
CLEAN_EXCEPTIONS = (
    '_ansible_verbose_always',  # for debug and other actions, to always expand data (pretty jsonification)
    '_ansible_item_label',  # to know actual 'item' variable
    '_ansible_no_log',  # jic we didnt clean up well enough, DON'T LOG
    '_ansible_verbose_override',  # controls display of ansible_facts, gathering would be very noise with -v otherwise
)


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
            # some squashed results (eg, dnf) are not dicts and can't be skipped individually
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

    def needs_debugger(self, globally_enabled=False):
        _debugger = self._task_fields.get('debugger')
        _ignore_errors = C.TASK_DEBUGGER_IGNORE_ERRORS and self._task_fields.get('ignore_errors')

        ret = False
        if globally_enabled and ((self.is_failed() and not _ignore_errors) or self.is_unreachable()):
            ret = True

        if _debugger in ('always',):
            ret = True
        elif _debugger in ('never',):
            ret = False
        elif _debugger in ('on_failed',) and self.is_failed() and not _ignore_errors:
            ret = True
        elif _debugger in ('on_unreachable',) and self.is_unreachable():
            ret = True
        elif _debugger in ('on_skipped',) and self.is_skipped():
            ret = True

        return ret

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

    def clean_copy(self):

        ''' returns 'clean' taskresult object '''

        # FIXME: clean task_fields, _task and _host copies
        result = TaskResult(self._host, self._task, {}, self._task_fields)

        # statuses are already reflected on the event type
        if result._task and result._task.action in C._ACTION_DEBUG:
            # debug is verbose by default to display vars, no need to add invocation
            ignore = _IGNORE + ('invocation',)
        else:
            ignore = _IGNORE

        subset = {}
        # preserve subset for later
        for sub in _SUB_PRESERVE:
            if sub in self._result:
                subset[sub] = {}
                for key in _SUB_PRESERVE[sub]:
                    if key in self._result[sub]:
                        subset[sub][key] = self._result[sub][key]

        if isinstance(self._task.no_log, bool) and self._task.no_log or self._result.get('_ansible_no_log', False):
            x = {"censored": "the output has been hidden due to the fact that 'no_log: true' was specified for this result"}

            # preserve full
            for preserve in _PRESERVE:
                if preserve in self._result:
                    x[preserve] = self._result[preserve]

            result._result = x
        elif self._result:
            result._result = module_response_deepcopy(self._result)

            # actually remove
            for remove_key in ignore:
                if remove_key in result._result:
                    del result._result[remove_key]

            # remove almost ALL internal keys, keep ones relevant to callback
            strip_internal_keys(result._result, exceptions=CLEAN_EXCEPTIONS)

        # keep subset
        result._result.update(subset)

        return result
