# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from base64 import b64decode
from json import loads as json_load

from ansible.errors import AnsibleAction, AnsibleActionDone, AnsibleActionFail
from ansible.module_utils._text import to_text
from ansible.module_utils.six import iteritems
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        try:
            if self._task.delegate_to and self._task.delegate_to not in C.LOCALHOST:
                result.update(self._execute_module(module_name='async_status', module_args=self._task.args, task_vars=task_vars, tmp=tmp))
                raise AnsibleActionDone()

            jid = self._task.args.get('pid')
            mode = self._task.args.get('mode', 'status')

            if not jid:
                raise AnsibleActionFail('Missing required field "jid"')

            # setup logging directory
            logdir = self._remote_expanduser(self._connection._shell.get_option('async_dir'))
            log_path = self._connection._shell.join_path(logdir, jid)

            slurpred = self._execute_module(module_name='slurp', module_args=dict(src=log_path), task_vars=task_vars, tmp=tmp)
            if slurpred.get('failed', False):
                raise AnsibleActionFail("could not find job file: %s" % log_path)

            if mode == 'cleanup':
                self._remove_tmp_path(log_path)
                raise AnsibleActionDone(result=dict(ansible_job_id=jid, erased=log_path))

            # NOT in cleanup mode, assume regular status mode
            # no remote kill mode currently exists, but probably should
            # consider log_path + ".pid" file and also unlink that above

            try:
                if slurpred['encoding'] == 'base64':
                    remote_data = b64decode(slurpred['content'])
                if remote_data is not None:
                    data = json_load(remote_data)
            except Exception:
                if not remote_data:
                    # file not written yet?  That means it is running
                    raise AnsibleActionDone(results=dict(results_file=log_path, ansible_job_id=jid, started=1, finished=0))
                else:
                    raise AnsibleActionFail("Could not parse job output: %s" % data,
                                            results=dict(ansible_job_id=jid, results_file=log_path, started=1, finished=1))

            if 'started' not in data:
                data['finished'] = 1
                data['ansible_job_id'] = jid
            elif 'finished' not in data:
                data['finished'] = 0

            # Fix error: TypeError: exit_json() keywords must be strings
            result.update(dict([(to_text(k), v) for k, v in iteritems(data)]))

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            if not self._task.until or result.get('finished', False):
                # remove a temporary path we created
                self._remove_tmp_path(self._connection._shell.tempdir)

        return result
