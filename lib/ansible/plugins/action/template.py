# Copyright: (c) 2015, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os
import shutil
import stat
import tempfile

from jinja2.defaults import (
    BLOCK_END_STRING,
    BLOCK_START_STRING,
    COMMENT_END_STRING,
    COMMENT_START_STRING,
    VARIABLE_END_STRING,
    VARIABLE_START_STRING,
)

from ansible import constants as C
from ansible.config.manager import ensure_type
from ansible.errors import AnsibleError, AnsibleActionFail
from ansible.module_utils.common.text.converters import to_bytes, to_text, to_native
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.template import trust_as_template
from ansible._internal._templating import _template_vars


class ActionModule(ActionBase):

    TRANSFERS_FILES = True
    DEFAULT_NEWLINE_SEQUENCE = "\n"

    def run(self, tmp=None, task_vars=None):
        """ handler for template operations """

        if task_vars is None:
            task_vars = dict()

        super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Options type validation
        # strings
        for s_type in ('src', 'dest', 'state', 'newline_sequence', 'variable_start_string', 'variable_end_string', 'block_start_string',
                       'block_end_string', 'comment_start_string', 'comment_end_string'):
            if s_type in self._task.args:
                value = ensure_type(self._task.args[s_type], 'string')
                if value is not None and not isinstance(value, str):
                    raise AnsibleActionFail("%s is expected to be a string, but got %s instead" % (s_type, type(value)))
                self._task.args[s_type] = value

        # booleans
        try:
            follow = boolean(self._task.args.get('follow', False), strict=False)
            trim_blocks = boolean(self._task.args.get('trim_blocks', True), strict=False)
            lstrip_blocks = boolean(self._task.args.get('lstrip_blocks', False), strict=False)
        except TypeError as e:
            raise AnsibleActionFail(to_native(e))

        # assign to local vars for ease of use
        source = self._task.args.get('src', None)
        dest = self._task.args.get('dest', None)
        state = self._task.args.get('state', None)
        newline_sequence = self._task.args.get('newline_sequence', self.DEFAULT_NEWLINE_SEQUENCE)
        variable_start_string = self._task.args.get('variable_start_string', VARIABLE_START_STRING)
        variable_end_string = self._task.args.get('variable_end_string', VARIABLE_END_STRING)
        block_start_string = self._task.args.get('block_start_string', BLOCK_START_STRING)
        block_end_string = self._task.args.get('block_end_string', BLOCK_END_STRING)
        comment_start_string = self._task.args.get('comment_start_string', COMMENT_START_STRING)
        comment_end_string = self._task.args.get('comment_end_string', COMMENT_END_STRING)
        output_encoding = self._task.args.get('output_encoding', 'utf-8') or 'utf-8'

        wrong_sequences = ["\\n", "\\r", "\\r\\n"]
        allowed_sequences = ["\n", "\r", "\r\n"]

        # We need to convert unescaped sequences to proper escaped sequences for Jinja2
        if newline_sequence in wrong_sequences:
            newline_sequence = allowed_sequences[wrong_sequences.index(newline_sequence)]

        try:
            # logical validation
            if state is not None:
                raise AnsibleActionFail("'state' cannot be specified on a template")
            elif source is None or dest is None:
                raise AnsibleActionFail("src and dest are required")
            elif newline_sequence not in allowed_sequences:
                raise AnsibleActionFail("newline_sequence needs to be one of: \n, \r or \r\n")
            else:
                try:
                    source = self._find_needle('templates', source)
                except AnsibleError as e:
                    raise AnsibleActionFail(to_text(e))

            mode = self._task.args.get('mode', None)
            if mode == 'preserve':
                mode = '0%03o' % stat.S_IMODE(os.stat(source).st_mode)

            # template the source data locally & get ready to transfer
            template_data = trust_as_template(self._loader.get_text_file_contents(source))

            # set jinja2 internal search path for includes
            searchpath = task_vars.get('ansible_search_path', [])
            searchpath.extend([self._loader._basedir, os.path.dirname(source)])

            # We want to search into the 'templates' subdir of each search path in
            # addition to our original search paths.
            newsearchpath = []
            for p in searchpath:
                newsearchpath.append(os.path.join(p, 'templates'))
                newsearchpath.append(p)
            searchpath = newsearchpath

            # add ansible 'template' vars
            temp_vars = task_vars.copy()
            temp_vars.update(_template_vars.generate_ansible_template_vars(
                path=self._task.args.get('src', None),
                fullpath=source,
                dest_path=dest,
                include_ansible_managed='ansible_managed' not in temp_vars,  # do not clobber ansible_managed when set by the user
            ))

            overrides = dict(
                block_start_string=block_start_string,
                block_end_string=block_end_string,
                variable_start_string=variable_start_string,
                variable_end_string=variable_end_string,
                comment_start_string=comment_start_string,
                comment_end_string=comment_end_string,
                trim_blocks=trim_blocks,
                lstrip_blocks=lstrip_blocks,
                newline_sequence=newline_sequence,
            )

            data_templar = self._templar.copy_with_new_env(searchpath=searchpath, available_variables=temp_vars)
            resultant = data_templar.template(template_data, escape_backslashes=False, overrides=overrides)

            if resultant is None:
                resultant = ''

            new_task = self._task.copy()
            # mode is either the mode from task.args or the mode of the source file if the task.args
            # mode == 'preserve'
            new_task.args['mode'] = mode

            # remove 'template only' options:
            for remove in ('newline_sequence', 'block_start_string', 'block_end_string', 'variable_start_string', 'variable_end_string',
                           'comment_start_string', 'comment_end_string', 'trim_blocks', 'lstrip_blocks', 'output_encoding'):
                new_task.args.pop(remove, None)

            local_tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)

            try:
                result_file = os.path.join(local_tempdir, os.path.basename(source))
                with open(to_bytes(result_file, errors='surrogate_or_strict'), 'wb') as f:
                    f.write(to_bytes(resultant, encoding=output_encoding, errors='surrogate_or_strict'))

                new_task.args.update(
                    dict(
                        src=result_file,
                        dest=dest,
                        follow=follow,
                    ),
                )
                # call with ansible.legacy prefix to eliminate collisions with collections while still allowing local override
                copy_action = self._shared_loader_obj.action_loader.get('ansible.legacy.copy',
                                                                        task=new_task,
                                                                        connection=self._connection,
                                                                        play_context=self._play_context,
                                                                        loader=self._loader,
                                                                        templar=self._templar,
                                                                        shared_loader_obj=self._shared_loader_obj)
                return copy_action.run(task_vars=task_vars)
            finally:
                shutil.rmtree(to_bytes(local_tempdir, errors='surrogate_or_strict'))
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)
