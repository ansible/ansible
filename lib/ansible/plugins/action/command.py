# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import tempfile
import shutil

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash
from ansible.module_utils.parsing.convert_bool import boolean


def _create_copy_or_empty_tempfile(path:str): 
    '''
    Create a tempfile containing a copy of the file at `path`.
    If `path` does not point to a file, create an empty tempfile.
    '''
    fd, tempfile_path = tempfile.mkstemp(dir=C.DEFAULT_LOCAL_TMP)
    if os.path.isfile(path):
        try:
            shutil.copy(path, tempfile_path)
        except Exception as err:
            os.remove(tempfile_path)
            raise Exception(err)
    return tempfile_path


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        self._supports_async = True
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        raw = boolean(self._task.args.get('raw', 'no'), strict=False)

        # make copies of files before command execution so that we can compare later
        if "modifies" in self._task.args and not raw:
            file_copy_paths_before = dict()
            for path in self._task.args['modifies']:
                file_copy_paths_before[path] = _create_copy_or_empty_tempfile(path)

        wrap_async = self._task.async_val and not self._connection.has_native_async
        # explicitly call `ansible.legacy.command` for backcompat to allow library/ override of `command` while not allowing
        # collections search for an unqualified `command` module
        results = merge_hash(results, self._execute_module(module_name='ansible.legacy.command', task_vars=task_vars, wrap_async=wrap_async))

        # compare current state of files to their before-command tempfile copies
        if "modifies" in self._task.args and not raw:
            if self._play_context.diff:
                results['diff'] = []
            results['changed'] = False
            for path in self._task.args['modifies']:
                copy_path_before = file_copy_paths_before[path]
                diff = self._get_diff_data(copy_path_before, path, task_vars)
                if self._play_context.diff:
                    results['diff'].append(diff)
                if not results['changed'] and diff['before'] != diff['after']:
                    results['changed'] = True
                os.remove(copy_path_before)

        if not wrap_async:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return results
