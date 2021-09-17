# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    _VALID_ARGS = frozenset(('jid', 'mode'))

    def _get_async_dir(self):

        # async directory based on the shell option
        async_dir = self.get_shell_option('async_dir', default="~/.ansible_async")

        return self._remote_expand_user(async_dir)

    def run(self, tmp=None, task_vars=None):

        results = super(ActionModule, self).run(tmp, task_vars)

        # initialize response
        results['started'] = results['finished'] = 0
        results['stdout'] = results['stderr'] = ''
        results['stdout_lines'] = results['stderr_lines'] = []

        # read params
        try:
            jid = self._task.args["jid"]
        except KeyError:
            raise AnsibleActionFail("jid is required", result=results)

        mode = self._task.args.get("mode", "status")

        results['ansible_job_id'] = jid
        async_dir = self._get_async_dir()
        log_path = self._connection._shell.join_path(async_dir, jid)

        if mode == 'cleanup':
            results['erased'] = log_path
        else:
            results['results_file'] = log_path
            results['started'] = 1

        module_args = dict(jid=jid, mode=mode, _async_dir=async_dir)
        results = merge_hash(results, self._execute_module(module_name='ansible.legacy.async_status', task_vars=task_vars, module_args=module_args))

        return results
