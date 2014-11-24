# (c) 2015, Brian Coca  <briancoca+dev@gmail.com>
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
from ansible import utils
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        options  = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))

        src = options.get('src', None)
        dest = options.get('dest', None)
        remote_src = utils.boolean(options.get('remote_src', 'yes'))

        if src is None:
            result = dict(failed=True, msg="src is required")
            return ReturnData(conn=conn, comm_ok=False, result=result)

        if remote_src:
            return self.runner._execute_module(conn, tmp, 'patch', module_args, inject=inject, complex_args=complex_args)

        # Source is local
        if '_original_file' in inject:
            src = utils.path_dwim_relative(inject['_original_file'], 'files', src, self.runner.basedir)
        else:
            src = utils.path_dwim(self.runner.basedir, src)

        tmp_src = tmp + src
        conn.put_file(src, tmp_src)

        if self.runner.become and self.runner.become_user != 'root':
            if not self.runner.noop_on_check(inject):
                self.runner._remote_chmod(conn, 'a+r', tmp_src, tmp)

        new_module_args = dict(
            src=tmp_src,
        )

        if self.runner.noop_on_check(inject):
            new_module_args['CHECKMODE'] = True

        module_args = utils.merge_module_args(module_args, new_module_args)

        return self.runner._execute_module(conn, tmp, 'patch', module_args, inject=inject, complex_args=complex_args)
