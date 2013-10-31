# (c) 2013, Michael DeHaan <michael.dehaan@gmail.com>
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
from ansible import utils

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def _assemble_from_fragments(src_path, delimiter=None):
        ''' assemble a file from a directory of fragments '''
        tmpfd, temp_path = tempfile.mkstemp()
        tmp = os.fdopen(tmpfd,'w')
        delimit_me = False
        for f in sorted(os.listdir(src_path)):
            fragment = "%s/%s" % (src_path, f)
            if delimit_me and delimiter:
                tmp.write(delimiter)
            if os.path.isfile(fragment):
                tmp.write(file(fragment).read())
            delimit_me = True
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
        remote_src = options.get('remote_src', True)

        if src is None or dest is None:
            result = dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        if remote_src:
            return self.runner._execute_module(conn, tmp, 'assemble', module_args, inject=inject, complex_args=complex_args)

        # Does all work assembling the file
        path = assemble_from_fragments(src, delimiter)

        pathmd5 = utils.md5s(path)
        remote_md5 = self.runner._remote_md5(conn, tmp, dest)

        if pathmd5 != remote_md5:
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
            if self.runner.sudo and self.runner.sudo_user != 'root':
                self.runner._low_level_exec_command(conn, "chmod a+r %s" % xfered, tmp)

            # run the copy module
            module_args = "%s src=%s dest=%s original_basename=%s" % (module_args, pipes.quote(xfered), pipes.quote(dest), pipes.quote(os.path.basename(src)))

            if self.runner.noop_on_check(inject):
                return ReturnData(conn=conn, comm_ok=True, result=dict(changed=True), diff=dict(before_header=dest, after_header=src, before=dest_contents, after=resultant))
            else:
                res = self.runner._execute_module(conn, tmp, 'copy', module_args, inject=inject, complex_args=complex_args)
                res.diff = dict(before=dest_contents, after=resultant)
                return res
        else:
            return self.runner._execute_module(conn, tmp, 'file', module_args, inject=inject, complex_args=complex_args)
