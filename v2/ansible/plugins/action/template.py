# (c) 2015, Michael DeHaan <michael.dehaan@gmail.com>
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import base64
import os

from ansible.plugins.action import ActionBase
from ansible.template import Templar
from ansible.utils.hashing import checksum_s

class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def get_checksum(self, tmp, dest, try_directory=False, source=None):
        remote_checksum = self._remote_checksum(tmp, dest)

        if remote_checksum in ('0', '2', '3', '4'):
            # Note: 1 means the file is not present which is fine; template
            # will create it.  3 means directory was specified instead of file
            if try_directory and remote_checksum == '3' and source:
                base = os.path.basename(source)
                dest = os.path.join(dest, base)
                remote_checksum = self.get_checksum(tmp, dest, try_directory=False)
                if remote_checksum not in ('0', '2', '3', '4'):
                    return remote_checksum

            result = dict(failed=True, msg="failed to checksum remote file."
                        " Checksum error code: %s" % remote_checksum)
            return result

        return remote_checksum

    def run(self, tmp=None, task_vars=dict()):
        ''' handler for template operations '''

        source = self._task.args.get('src', None)
        dest   = self._task.args.get('dest', None)

        if (source is None and 'first_available_file' not in task_vars) or dest is None:
            return dict(failed=True, msg="src and dest are required")

        if tmp is None:
            tmp = self._make_tmp_path()

        ##################################################################################################
        # FIXME: this all needs to be sorted out
        ##################################################################################################
        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        #if 'first_available_file' in task_vars:
        #    found = False
        #    for fn in task_vars.get('first_available_file'):
        #        fn_orig = fn
        #        fnt = template.template(self.runner.basedir, fn, task_vars)
        #        fnd = utils.path_dwim(self.runner.basedir, fnt)
        #        if not os.path.exists(fnd) and '_original_file' in task_vars:
        #            fnd = utils.path_dwim_relative(task_vars['_original_file'], 'templates', fnt, self.runner.basedir, check=False)
        #        if os.path.exists(fnd):
        #            source = fnd
        #            found = True
        #            break
        #    if not found:
        #        result = dict(failed=True, msg="could not find src in first_available_file list")
        #        return ReturnData(conn=conn, comm_ok=False, result=result)
        #else:
        if 1:
            if self._task._role is not None:
                source = self._loader.path_dwim_relative(self._task._role._role_path, 'templates', source)
            else:
                source = self._loader.path_dwim(source)
        ##################################################################################################
        # END FIXME
        ##################################################################################################

        # Expand any user home dir specification
        dest = self._remote_expand_user(dest, tmp)

        directory_prepended = False
        if dest.endswith(os.sep):
            directory_prepended = True
            base = os.path.basename(source)
            dest = os.path.join(dest, base)

        # template the source data locally & get ready to transfer
        templar = Templar(loader=self._loader, variables=task_vars)
        try:
            with open(source, 'r') as f:
                template_data = f.read()
            resultant = templar.template(template_data, preserve_trailing_newlines=True)
        except Exception as e:
            return dict(failed=True, msg=type(e).__name__ + ": " + str(e))

        local_checksum = checksum_s(resultant)
        remote_checksum = self.get_checksum(tmp, dest, not directory_prepended, source=source)
        if isinstance(remote_checksum, dict):
            # Error from remote_checksum is a dict.  Valid return is a str
            return remote_checksum

        if local_checksum != remote_checksum:
            # if showing diffs, we need to get the remote value
            dest_contents = ''

            # FIXME: still need to implement diff mechanism
            #if self.runner.diff:
            #    # using persist_files to keep the temp directory around to avoid needing to grab another
            #    dest_result = self.runner._execute_module(conn, tmp, 'slurp', "path=%s" % dest, task_vars=task_vars, persist_files=True)
            #    if 'content' in dest_result.result:
            #        dest_contents = dest_result.result['content']
            #        if dest_result.result['encoding'] == 'base64':
            #            dest_contents = base64.b64decode(dest_contents)
            #        else:
            #            raise Exception("unknown encoding, failed: %s" % dest_result.result)
 
            xfered = self._transfer_data(self._shell.join_path(tmp, 'source'), resultant)

            # fix file permissions when the copy is done as a different user
            if self._connection_info.become and self._connection_info.become_user != 'root':
                self._remote_chmod('a+r', xfered, tmp)

            # run the copy module
            new_module_args = self._task.args.copy()
            new_module_args.update(
               dict(
                   src=xfered,
                   dest=dest,
                   original_basename=os.path.basename(source),
                   follow=True,
                ),
            )

            # FIXME: noop stuff needs to be sorted out
            #if self.runner.noop_on_check(task_vars):
            #    return ReturnData(conn=conn, comm_ok=True, result=dict(changed=True), diff=dict(before_header=dest, after_header=source, before=dest_contents, after=resultant))
            #else:
            #    res = self.runner._execute_module(conn, tmp, 'copy', module_args_tmp, task_vars=task_vars, complex_args=complex_args)
            #    if res.result.get('changed', False):
            #        res.diff = dict(before=dest_contents, after=resultant)
            #    return res

            result = self._execute_module(module_name='copy', module_args=new_module_args)
            if result.get('changed', False):
                result['diff'] = dict(before=dest_contents, after=resultant)
            return result

        else:
            # when running the file module based on the template data, we do
            # not want the source filename (the name of the template) to be used,
            # since this would mess up links, so we clear the src param and tell
            # the module to follow links.  When doing that, we have to set
            # original_basename to the template just in case the dest is
            # a directory.
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=None,
                    original_basename=os.path.basename(source),
                    follow=True,
                ),
            )

            # FIXME: this may not be required anymore, as the checkmod params
            #        should be in the regular module args?
            # be sure to task_vars the check mode param into the module args and
            # rely on the file module to report its changed status
            #if self.runner.noop_on_check(task_vars):
            #    new_module_args['CHECKMODE'] = True

            return self._execute_module(module_name='file', module_args=new_module_args)

