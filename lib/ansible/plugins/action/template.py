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
import datetime
import os
import time

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.hashing import checksum_s
from ansible.utils.unicode import to_bytes

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
        faf    = self._task.first_available_file

        if (source is None and faf is not None) or dest is None:
            return dict(failed=True, msg="src and dest are required")

        if tmp is None:
            tmp = self._make_tmp_path()

        if faf:
            #FIXME: issue deprecation warning for first_available_file, use with_first_found or lookup('first_found',...) instead
            found = False
            for fn in faf:
                fn_orig = fn
                fnt = self._templar.template(fn)
                fnd = self._loader.path_dwim(self._task._role_._role_path, 'templates', fnt)

                if not os.path.exists(fnd):
                    of = task_vars.get('_original_file', None)
                    if of is not None:
                        fnd = self._loader.path_dwim(self._task._role_._role_path, 'templates', of)

                if os.path.exists(fnd):
                    source = fnd
                    found = True
                    break
            if not found:
                return dict(failed=True, msg="could not find src in first_available_file list")
        else:
            if self._task._role is not None:
                source = self._loader.path_dwim_relative(self._task._role._role_path, 'templates', source)
            else:
                source = self._loader.path_dwim(source)

        # Expand any user home dir specification
        dest = self._remote_expand_user(dest, tmp)

        directory_prepended = False
        if dest.endswith(os.sep):
            directory_prepended = True
            base = os.path.basename(source)
            dest = os.path.join(dest, base)

        # template the source data locally & get ready to transfer
        try:
            with open(source, 'r') as f:
                template_data = f.read()

            try:
                template_uid = pwd.getpwuid(os.stat(source).st_uid).pw_name
            except:
                template_uid = os.stat(source).st_uid

            vars = task_vars.copy()
            vars['template_host']     = os.uname()[1]
            vars['template_path']     = source
            vars['template_mtime']    = datetime.datetime.fromtimestamp(os.path.getmtime(source))
            vars['template_uid']      = template_uid
            vars['template_fullpath'] = os.path.abspath(source)
            vars['template_run_date'] = datetime.datetime.now()

            managed_default = C.DEFAULT_MANAGED_STR
            managed_str = managed_default.format(
                host = vars['template_host'],
                uid  = vars['template_uid'],
                file = to_bytes(vars['template_path'])
            )
            vars['ansible_managed'] = time.strftime(
                managed_str,
                time.localtime(os.path.getmtime(source))
            )

            old_vars = self._templar._available_variables
            self._templar.set_available_variables(vars)
            resultant = self._templar.template(template_data, preserve_trailing_newlines=True)
            self._templar.set_available_variables(old_vars)
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

            xfered = self._transfer_data(self._connection._shell.join_path(tmp, 'source'), resultant)

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

            result = self._execute_module(module_name='copy', module_args=new_module_args, task_vars=task_vars)
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

            return self._execute_module(module_name='file', module_args=new_module_args, task_vars=task_vars)

