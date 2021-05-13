# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import tempfile

from ansible.constants import config
from ansible.errors import AnsibleError, AnsibleActionFail, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils._text import to_native
from ansible.module_utils.six import iteritems
from ansible.plugins.action import ActionBase


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

    def run(self, tmp=None, task_vars=None):

        results = super(ActionModule, self).run(tmp, task_vars)
        results['stdout'] = results['stderr'] = ''
        results['stdout_lines'] = results['stderr_lines'] = []

        try:
            jid = self._task.args["jid"]
        except KeyError:
            raise AnsibleActionFail("jid is required")

        mode = self._task.args.get("mode", "status")

        async_dir = self._get_async_dir()

        log_path = self._connection._shell.join_path(async_dir, jid)

        cleanup = False

        results['ansible_job_id'] = jid

        if mode == 'cleanup':
            cleanup = True
        else:
            results['results_file'] = log_path
            results['started'] = 1
            results['finished'] = 0


            # local tempfile to copy job file to
            fd, tmpfile = tempfile.mkstemp(prefix='_async_%s' % jid, dir=config.get_config_value('DEFAULT_LOCAL_TMP'))

            try:
                self._connection.fetch_file(log_path, tmpfile)
            except AnsibleConnectionFailure:
                raise
            except AnsibleFileNotFound as e:
                raise AnsibleActionFail("could not find job", orig_exc=e)
            except AnsibleError as e:
                raise AnsibleActionFail("failed to fetch the job file: %s" % to_native(e), orig_exc=e)

            try:
                with open(tmpfile) as f:
                    file_data = f.read()
                    data = json.loads(file_data)

                if 'started' not in data:
                    data['finished'] = 1
                    data['ansible_job_id'] = jid
                    cleanup = True
                elif 'finished' not in data:
                    data['finished'] = 0

                results.update(dict([(to_native(k), v) for k, v in iteritems(data)]))

            except Exception:
                if file_data:
                    cleanup = True
                    results['finished'] = 1
                    results['failed'] = True
                    results['msg'] = "Could not parse job output: %s" % to_native(file_data, errors='surrogate_or_strict')

        if cleanup:
            self._remove_tmp_path(log_path, force=True)
            results['erased'] = log_path

        return results
