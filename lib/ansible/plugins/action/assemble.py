# (c) 2013-2014, Michael DeHaan <michael.dehaan@gmail.com>
#           Stephen Fromm <sfromm@gmail.com>
#           Brian Coca  <briancoca+dev@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import os.path
import tempfile
import re

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean
from ansible.utils.hashing import checksum_s


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def _assemble_from_fragments(self, src_path, delimiter=None, compiled_regexp=None, ignore_hidden=False):
        ''' assemble a file from a directory of fragments '''

        tmpfd, temp_path = tempfile.mkstemp()
        tmp = os.fdopen(tmpfd,'w')
        delimit_me = False
        add_newline = False

        for f in sorted(os.listdir(src_path)):
            if compiled_regexp and not compiled_regexp.search(f):
                continue
            fragment = "%s/%s" % (src_path, f)
            if not os.path.isfile(fragment) or (ignore_hidden and os.path.basename(fragment).startswith('.')):
                continue
            fragment_content = file(fragment).read()

            # always put a newline between fragments if the previous fragment didn't end with a newline.
            if add_newline:
                tmp.write('\n')

            # delimiters should only appear between fragments
            if delimit_me:
                if delimiter:
                    # un-escape anything like newlines
                    delimiter = delimiter.decode('unicode-escape')
                    tmp.write(delimiter)
                    # always make sure there's a newline after the
                    # delimiter, so lines don't run together
                    if delimiter[-1] != '\n':
                        tmp.write('\n')

            tmp.write(fragment_content)
            delimit_me = True
            if fragment_content.endswith('\n'):
                add_newline = False
            else:
                add_newline = True

        tmp.close()
        return temp_path

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if self._play_context.check_mode:
            result['skipped'] = True
            result['msg'] = "skipped, this module does not support check_mode."
            return result

        src        = self._task.args.get('src', None)
        dest       = self._task.args.get('dest', None)
        delimiter  = self._task.args.get('delimiter', None)
        remote_src = self._task.args.get('remote_src', 'yes')
        regexp     = self._task.args.get('regexp', None)
        ignore_hidden = self._task.args.get('ignore_hidden', False)

        if src is None or dest is None:
            result['failed'] = True
            result['msg'] = "src and dest are required"
            return result

        if boolean(remote_src):
            result.update(self._execute_module(tmp=tmp, task_vars=task_vars))
            return result

        elif self._task._role is not None:
            src = self._loader.path_dwim_relative(self._task._role._role_path, 'files', src)
        else:
            src = self._loader.path_dwim_relative(self._loader.get_basedir(), 'files', src)

        _re = None
        if regexp is not None:
            _re = re.compile(regexp)

        if not os.path.isdir(src):
            result['failed'] = True
            result['msg'] = "Source (%s) is not a directory" % src
            return result

        # Does all work assembling the file
        path = self._assemble_from_fragments(src, delimiter, _re, ignore_hidden)

        path_checksum = checksum_s(path)
        dest = self._remote_expand_user(dest)
        remote_checksum = self._remote_checksum(dest, all_vars=task_vars)

        diff = {}
        if path_checksum != remote_checksum:
            resultant = file(path).read()

            if self._play_context.diff:
                diff = self._get_diff_data(dest, path, task_vars)

            xfered = self._transfer_data('src', resultant)

            # fix file permissions when the copy is done as a different user
            if self._play_context.become and self._play_context.become_user != 'root':
                self._remote_chmod('a+r', xfered)

            # run the copy module

            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=xfered,
                    dest=dest,
                    original_basename=os.path.basename(src),
                )
            )

            res = self._execute_module(module_name='copy', module_args=new_module_args, task_vars=task_vars, tmp=tmp)
            if diff:
                res['diff'] = diff
            result.update(res)
            return result
        else:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=xfered,
                    dest=dest,
                    original_basename=os.path.basename(src),
                )
            )

            result.update(self._execute_module(module_name='file', module_args=new_module_args, task_vars=task_vars, tmp=tmp))
            return result
