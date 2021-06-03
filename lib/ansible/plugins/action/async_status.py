# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import tempfile
import time

from ansible.constants import config
from ansible.errors import AnsibleError, AnsibleActionFail, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash


class ActionModule(ActionBase):

    _VALID_ARGS = frozenset(('jid', 'mode'))

    def _get_async_dir(self):

        # async directory based on the shell option
        async_dir = self.get_shell_option('async_dir', default="~/.ansible_async")

        # for backwards compatibility we need to get the dir from
        # ANSIBLE_ASYNC_DIR that is defined in the environment. This is
        # deprecated and will be removed in favour of shell options
        env_async_dir = [e for e in self._task.environment if "ANSIBLE_ASYNC_DIR" in e]
        if len(env_async_dir) > 0:
            async_dir = env_async_dir[0]['ANSIBLE_ASYNC_DIR']
            msg = "Setting the async dir from the environment keyword " \
                  "ANSIBLE_ASYNC_DIR is deprecated. Set the async_dir " \
                  "shell option instead"
            self._display.deprecated(msg, "2.12", collection_name='ansible.builtin')

        return self._remote_expand_user(async_dir)

    def _update_results_with_job_file(self, jid, log_path, results):

        # local tempfile to copy job file to, using local tmp which is auto cleaned on exit
        fd, tmpfile = tempfile.mkstemp(prefix='_async_%s' % jid, dir=config.get_config_value('DEFAULT_LOCAL_TMP'))

        attempts = 0
        while True:
            try:
                self._connection.fetch_file(log_path, tmpfile)
            except AnsibleConnectionFailure:
                raise
            except AnsibleFileNotFound as e:
                if attempts > 3:
                    raise AnsibleActionFail("Could not find job file on remote: %s" % to_native(e), orig_exc=e, result=results)
            except AnsibleError as e:
                if attempts > 3:
                    raise AnsibleActionFail("Could not fetch the job file from remote: %s" % to_native(e), orig_exc=e, result=results)

            try:
                with open(tmpfile) as f:
                    file_data = f.read()
            except (IOError, OSError):
                pass

            if file_data:
                break
            elif attempts > 3:
                raise AnsibleActionFail("Unable to fetch a usable job file", result=results)

            attempts += 1
            time.sleep(attempts * 0.2)

        try:
            data = json.loads(file_data)
        except Exception:
            results['finished'] = 1
            results['failed'] = True
            results['msg'] = "Could not parse job output: %s" % to_native(file_data, errors='surrogate_or_strict')

        if 'started' not in data:
            data['finished'] = 1
            data['ansible_job_id'] = jid

        results.update(dict([(to_native(k), v) for k, v in iteritems(data)]))

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
            self._remove_tmp_path(log_path, force=True)
            results['erased'] = log_path
        else:
            results['results_file'] = log_path
            results['started'] = 1

            if getattr(self._connection._shell, '_IS_WINDOWS', False):
                # TODO: eventually fix so we can get remote user (%USERPROFILE%) like we get ~/ for posix
                module_args = dict(jid=jid, mode=mode, _async_dir=async_dir)
                results = merge_hash(results, self._execute_module(module_name='ansible.legacy.async_status', task_vars=task_vars, module_args=module_args))
            else:
                # fetch remote file and read locally
                self._update_results_with_job_file(jid, log_path, results)

        return results
