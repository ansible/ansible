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
import pipes
import shutil
import tempfile
import base64
import re

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean
from ansible.utils.hashing import checksum_s

class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def _assemble_from_fragments(self, src_path, delimiter=None, compiled_regexp=None):
        ''' assemble a file from a directory of fragments '''

        tmpfd, temp_path = tempfile.mkstemp()
        tmp = os.fdopen(tmpfd,'w')
        delimit_me = False
        add_newline = False

        for f in sorted(os.listdir(src_path)):
            if compiled_regexp and not compiled_regexp.search(f):
                continue
            fragment = "%s/%s" % (src_path, f)
            if not os.path.isfile(fragment):
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

    def run(self, tmp=None, task_vars=dict()):

        src        = self._task.args.get('src', None)
        dest       = self._task.args.get('dest', None)
        delimiter  = self._task.args.get('delimiter', None)
        remote_src = self._task.args.get('remote_src', 'yes')
        regexp     = self._task.args.get('regexp', None)

        if src is None or dest is None:
            return dict(failed=True, msg="src and dest are required")

        if boolean(remote_src):
            return self._execute_module(tmp=tmp)
        elif self._task._role is not None:
            src = self._loader.path_dwim_relative(self._task._role._role_path, 'files', src)
        else:
            # the source is local, so expand it here
            src = self._loader.path_dwim(os.path.expanduser(src))

        _re = None
        if regexp is not None:
            _re = re.compile(regexp)

        # Does all work assembling the file
        path = self._assemble_from_fragments(src, delimiter, _re)

        path_checksum = checksum_s(path)
        dest = self._remote_expand_user(dest, tmp)
        remote_checksum = self._remote_checksum(tmp, dest)

        if path_checksum != remote_checksum:
            resultant = file(path).read()
            # FIXME: diff needs to be moved somewhere else
            #if self.runner.diff:
            #    dest_result = self._execute_module(module_name='slurp', module_args=dict(path=dest), tmp=tmp, persist_files=True)
            #    if 'content' in dest_result:
            #        dest_contents = dest_result['content']
            #        if dest_result['encoding'] == 'base64':
            #            dest_contents = base64.b64decode(dest_contents)
            #        else:
            #            raise Exception("unknown encoding, failed: %s" % dest_result)
            xfered = self._transfer_data('src', resultant)

            # fix file permissions when the copy is done as a different user
            if self._connection_info.become and self._connection_info.become_user != 'root':
                self._remote_chmod('a+r', xfered, tmp)

            # run the copy module
            
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=xfered,
                    dest=dest,
                    original_basename=os.path.basename(src),
                )
            )

            # FIXME: checkmode stuff
            #if self.runner.noop_on_check(inject):
            #    return ReturnData(conn=conn, comm_ok=True, result=dict(changed=True), diff=dict(before_header=dest, after_header=src, after=resultant))
            #else:
            #    res = self.runner._execute_module(conn, tmp, 'copy', module_args_tmp, inject=inject)
            #    res.diff = dict(after=resultant)
            #    return res
            res = self._execute_module(module_name='copy', module_args=new_module_args, tmp=tmp)
            #res.diff = dict(after=resultant)
            return res
        else:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=xfered,
                    dest=dest,
                    original_basename=os.path.basename(src),
                )
            )

            return self._execute_module(module_name='file', module_args=new_module_args, tmp=tmp)
