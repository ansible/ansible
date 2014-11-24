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

import os
import os.path
import pipes
import shutil
import tempfile
import base64
import re
from ansible import utils
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

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

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        # load up options
        options  = {}
        if complex_args:
            options.update(complex_args)

        options.update(utils.parse_kv(module_args))

        src = options.get('src', None)
        dest = options.get('dest', None)
        delimiter = options.get('delimiter', None)
        remote_src = utils.boolean(options.get('remote_src', 'yes'))
        regexp = options.get('regexp', None)


        if src is None or dest is None:
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        if remote_src:
            return self.runner._execute_module(conn, tmp, 'assemble', module_args, inject=inject, complex_args=complex_args)
        elif '_original_file' in inject:
            src = utils.path_dwim_relative(inject['_original_file'], 'files', src, self.runner.basedir)
        else:
            # the source is local, so expand it here
            src = os.path.expanduser(src)

        _re = None
        if regexp is not None:
            _re = re.compile(regexp)

        # Does all work assembling the file
        path = self._assemble_from_fragments(src, delimiter, _re)

        path_checksum = utils.checksum_s(path)
        dest = self.runner._remote_expand_user(conn, dest, tmp)
        remote_checksum = self.runner._remote_checksum(conn, tmp, dest, inject)

        if path_checksum != remote_checksum:
            resultant = file(path).read()
            if self.runner.diff:
                dest_result = self.runner._execute_module(conn, tmp, 'slurp', "path=%s" % dest, inject=inject, persist_files=True)
                if 'content' in dest_result.result:
                    dest_contents = dest_result.result['content']
                    if dest_result.result['encoding'] == 'base64':
                        dest_contents = base64.b64decode(dest_contents)
                    else:
                        raise Exception("unknown encoding, failed: %s" % dest_result.result)
            xfered = self.runner._transfer_str(conn, tmp, 'src', resultant)

            # fix file permissions when the copy is done as a different user
            if self.runner.become and self.runner.become_user != 'root':
                self.runner._remote_chmod(conn, 'a+r', xfered, tmp)

            # run the copy module
            new_module_args = dict(
                src=xfered,
                dest=dest,
                original_basename=os.path.basename(src),
            )
            module_args_tmp = utils.merge_module_args(module_args, new_module_args)

            if self.runner.noop_on_check(inject):
                return ReturnData(conn=conn, comm_ok=True, result=dict(changed=True), diff=dict(before_header=dest, after_header=src, after=resultant))
            else:
                res = self.runner._execute_module(conn, tmp, 'copy', module_args_tmp, inject=inject)
                res.diff = dict(after=resultant)
                return res
        else:
            new_module_args = dict(
                src=xfered,
                dest=dest,
                original_basename=os.path.basename(src),
            )

            # make sure checkmod is passed on correctly
            if self.runner.noop_on_check(inject):
                new_module_args['CHECKMODE'] = True

            module_args_tmp = utils.merge_module_args(module_args, new_module_args)

            return self.runner._execute_module(conn, tmp, 'file', module_args_tmp, inject=inject)
