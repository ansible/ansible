# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import shutil
import stat
import tempfile
import re

from ansible import constants as C
from ansible.config.manager import ensure_type
from ansible.errors import AnsibleError, AnsibleFileNotFound, AnsibleAction, AnsibleActionFail
from ansible.module_utils._text import to_bytes, to_text, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def copy_local_file_to_remote(self,local_path,remote_path,task_vars):
         # create a copy of the current task so we can adjust it and re-use it to run the moudle
        task_copy_new_file_contents = self._task.copy()

        task_copy_new_file_contents.args.clear()

        try:
            task_copy_new_file_contents.args.update(
                dict(
                    src=local_path,
                    dest=remote_path,
                ),
            )      
            action_copy_new_file_contents = self._shared_loader_obj.action_loader.get('copy',
                                                                    task=task_copy_new_file_contents,
                                                                    connection=self._connection,
                                                                    play_context=self._play_context,
                                                                    loader=self._loader,
                                                                    templar=self._templar,
                                                                    shared_loader_obj=self._shared_loader_obj)

        except AnsibleAction as e:
            action_plugin_result.update(e.action_plugin_result)

        return action_copy_new_file_contents.run(task_vars=task_vars)

    def copy_remote_file_to_local(self,remote_path,local_path,task_vars):
         # create a copy of the current task so we can adjust it and re-use it to run the moudle
        task_fetch_original_file_contents = self._task.copy()

        task_fetch_original_file_contents.args.clear()

        try:
            task_fetch_original_file_contents.args.update(
                dict(
                    src=remote_path,
                    dest=local_path,
                    flat=True
                ),
            )      
            action_fetch_original_file_contents = self._shared_loader_obj.action_loader.get('fetch',
                                                                    task=task_fetch_original_file_contents,
                                                                    connection=self._connection,
                                                                    play_context=self._play_context,
                                                                    loader=self._loader,
                                                                    templar=self._templar,
                                                                    shared_loader_obj=self._shared_loader_obj)

        except AnsibleAction as e:
            action_plugin_result.update(e.action_plugin_result)

        return action_fetch_original_file_contents.run(task_vars=task_vars)
        

    def run(self, tmp=None, task_vars=None):
        ''' handler for replace operations '''

        if task_vars is None:
            task_vars = dict()

        action_plugin_result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Options type validation
        # stings
        for s_type in ('path', 'regexp', 'replace', 'after', 'before', 'validate',
                       'encoding'):
            if s_type in self._task.args:
                value = ensure_type(self._task.args[s_type], 'string')
                if value is not None and not isinstance(value, string_types):
                    raise AnsibleActionFail("%s is expected to be a string, but got %s instead" % (s_type, type(value)))
                self._task.args[s_type] = value

        # booleans
        try:
            backup = boolean(self._task.args.get('backup', False), strict=False)
        except TypeError as e:
            raise AnsibleActionFail(to_native(e))

        # assign to local vars for ease of use
       
        path = self._task.args.get('path')
        encoding = self._task.args.get('encoding')
        res_args = dict()

        after = to_text(self._task.args.get('after'), errors='surrogate_or_strict', nonstring='passthru')
        before = to_text(self._task.args.get('before'), errors='surrogate_or_strict', nonstring='passthru')
        regexp = to_text(self._task.args.get('regexp'), errors='surrogate_or_strict', nonstring='passthru')
        replace = to_text(self._task.args.get('replace'), errors='surrogate_or_strict', nonstring='passthru')


        # Next we need to `stat` the remote path to ensure it's valid (porting https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/files/replace.py#L240)

            #make sure not a directory
            # make sure file exists

        # Next we need to get the contents of the remote file (maybe this step would supersede the previous?)
        local_tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
        local_copy_of_original_file = os.path.join(local_tempdir, os.path.basename(path))
        
        copy_remote_to_acs_result = self.copy_remote_file_to_local(path,local_copy_of_original_file,task_vars)
        action_plugin_result['original_checksum'] = copy_remote_to_acs_result['checksum']

       
        print (copy_remote_to_acs_result)

        with open(local_copy_of_original_file, 'rb') as f:
            try:
                original_file_contents = to_text(f.read(), errors='surrogate_or_strict')
            except UnicodeError:
                raise AnsibleActionFail("Template source files must be utf-8 encoded")

        # At this point, we've copied the file locally, and read it into original_file_contents

        # Next we need to run the "replace" operation
        pattern = u''
        if after and before:
            pattern = u'%s(?P<subsection>.*?)%s' % (after, before)
        elif after:
            pattern = u'%s(?P<subsection>.*)' % after
        elif before:
            pattern = u'(?P<subsection>.*)%s' % before

        if pattern:
            section_re = re.compile(pattern, re.DOTALL)
            match = re.search(section_re, original_file_contents)
            if match:
                section = match.group('subsection')
                indices = [match.start('subsection'), match.end('subsection')]
            else:
                res_args['msg'] = 'Pattern for before/after params did not match the given file: %s' % pattern
                res_args['changed'] = False
                module.exit_json(**res_args)
        else:
            section = original_file_contents
        
        mre = re.compile(regexp, re.MULTILINE)
        replace_result = re.subn(mre, replace, section, 0)
        if replace_result[1] > 0 and section != replace_result[0]:
            if pattern:
                replace_result = (original_file_contents[:indices[0]] + replace_result[0] + original_file_contents[indices[1]:], replace_result[1])
            msg = '%s replacements made' % replace_result[1]
            changed = True
            if self._play_context.diff:
                res_args['diff'] = {
                    'before_header': path,
                    'before': original_file_contents,
                    'after_header': path,
                    'after': replace_result[0],
                }
        else:
            msg = ''
            changed = False

        print("New File contents: " + replace_result[0])

        if changed and not self._play_context.check_mode:
            with open(local_copy_of_original_file, 'wb') as f:
                try:
                    f.write(to_bytes(replace_result[0], encoding="utf-8", errors='surrogate_or_strict'))
                except UnicodeError:
                    raise AnsibleActionFail("Template source files must be utf-8 encoded")
            copy_acs_to_remote_result = self.copy_local_file_to_remote(local_copy_of_original_file,path,task_vars)
            action_plugin_result['new_checksum'] = copy_acs_to_remote_result['checksum']

        action_plugin_result["changed"] = changed
        
        return action_plugin_result