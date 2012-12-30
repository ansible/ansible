# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import pwd
import random
import traceback
import tempfile

import ansible.constants as C
from ansible import utils
from ansible import errors
from ansible import module_common
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject):
        ''' handler for file transfer operations '''

        # load up options
        options = utils.parse_kv(module_args)
        source  = options.get('src', None)
        dest    = options.get('dest', None)

        if dest.endswith("/"):
            base = os.path.basename(source)
            dest = os.path.join(dest, base)

        if (source is None and not 'first_available_file' in inject) or dest is None:
            result=dict(failed=True, msg="src and dest are required")
            return ReturnData(conn=conn, result=result)

        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        if 'first_available_file' in inject:
            found = False
            for fn in inject.get('first_available_file'):
                fn = utils.template(self.runner.basedir, fn, inject)
                fn = utils.path_dwim(self.runner.basedir, fn)
                if os.path.exists(fn):
                    source = fn
                    found = True
                    break
            if not found:
                results=dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, result=results)

        source = utils.template(self.runner.basedir, source, inject)
        source = utils.path_dwim(self.runner.basedir, source)

        source_files = []
        results = []

        if os.path.isdir(source):
            for base_path, sub_folders, files in os.walk(source):
                for file in files:
                    source_files.append(os.path.join(base_path, file))
        else:
            source_files.append(source)

        changed = False

        for source_file in source_files:
            # We need to get a new tmp path for each file, otherwise the copy module deletes the folder.
            tmp = self.runner._make_tmp_path(conn)
            local_md5 = utils.md5(source_file)

            if local_md5 is None:
                result = dict(failed=True, msg="could not find src=%s" % source_file)
                return ReturnData(conn=conn, result=result)

            remote_md5 = self.runner._remote_md5(conn, tmp, dest)

            exec_rc = None
            if local_md5 != remote_md5:
                # transfer the file to a remote tmp location
                tmp_src = tmp + os.path.basename(source_file)
                conn.put_file(source_file, tmp_src)
                # fix file permissions when the copy is done as a different user
                if self.runner.sudo and self.runner.sudo_user != 'root':
                    self.runner._low_level_exec_command(conn, "chmod a+r %s" % tmp_src, tmp)

                # run the copy module
                module_args = "%s src=%s" % (module_args, tmp_src)
                module_return = self.runner._execute_module(conn, tmp, 'copy', module_args, inject=inject)

            else:
                # no need to transfer the file, already correct md5, but still need to call
                # the file module in case we want to change attributes

                tmp_src = tmp + os.path.basename(source_file)
                module_args = "%s src=%s" % (module_args, tmp_src)
                module_return = self.runner._execute_module(conn, tmp, 'file', module_args, inject=inject)

            module_result = module_return.result
            if 'failed' in module_result and module_result['failed'] == True:
                return module_return
            if 'changed' in module_result and module_result['changed'] == True:
                changed = True

        res_args = dict(
            dest=dest, src=source, changed=changed
        )

        return ReturnData(conn=conn, result=res_args)
