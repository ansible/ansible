# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2013, Dylan Martin <dmartin@seattlecentral.edu>
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

import os
import pipes

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=dict()):
        ''' handler for unarchive operations '''

        source  = self._task.args.get('src', None)
        dest    = self._task.args.get('dest', None)
        copy    = self._task.args.get('copy', True)
        creates = self._task.args.get('creates', None)

        if source is None or dest is None:
            return dict(failed=True, msg="src (or content) and dest are required")

        if not tmp:
            tmp = self._make_tmp_path()

        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            module_args_tmp = "path=%s" % creates
            result = self._execute_module(module_name='stat', module_args=dict(path=creates))
            stat = result.get('stat', None)
            if stat and stat.get('exists', False):
                return dict(skipped=True, msg=("skipped, since %s exists" % creates))

        dest = self._remote_expand_user(dest, tmp) # CCTODO: Fix path for Windows hosts.
        source = os.path.expanduser(source)

        if copy:
            # FIXME: the original file stuff needs to be reworked
            if '_original_file' in task_vars:
                source = self._loader.path_dwim_relative(task_vars['_original_file'], 'files', source)
            else:
                source = self._loader.path_dwim(source)

        remote_checksum = self._remote_checksum(tmp, dest)
        if remote_checksum != '3':
            return dict(failed=True, msg="dest '%s' must be an existing dir" % dest)
        elif remote_checksum == '4':
            return dict(failed=True, msg="python isn't present on the system.  Unable to compute checksum")

        if copy:
            # transfer the file to a remote tmp location
            tmp_src = tmp + 'source'
            self._connection.put_file(source, tmp_src)

        # handle diff mode client side
        # handle check mode client side
        # fix file permissions when the copy is done as a different user
        if copy:
            if self._connection_info.become and self._connection_info.become_user != 'root':
                # FIXME: noop stuff needs to be reworked
                #if not self.runner.noop_on_check(task_vars):
                #    self.runner._remote_chmod(conn, 'a+r', tmp_src, tmp)
                self._remote_chmod(tmp, 'a+r', tmp_src)

            # Build temporary module_args.
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    src=tmp_src,
                    original_basename=os.path.basename(source),
                ),
            )

            # make sure checkmod is passed on correctly
            # FIXME: noop again, probably doesn't need to be done here anymore?
            #if self.runner.noop_on_check(task_vars):
            #    new_module_args['CHECKMODE'] = True

        else:
            new_module_args = self._task.args.copy()
            new_module_args.update(
                dict(
                    original_basename=os.path.basename(source),
                ),
            )
            # make sure checkmod is passed on correctly
            # FIXME: noop again, probably doesn't need to be done here anymore?
            #if self.runner.noop_on_check(task_vars):
            #    module_args += " CHECKMODE=True"

        # execute the unarchive module now, with the updated args
        return self._execute_module(module_args=new_module_args)

