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

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean


class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' handler for unarchive operations '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        source  = self._task.args.get('src', None)
        copy    = boolean(self._task.args.get('copy', True))
        creates = self._task.args.get('creates', None)

        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            result = self._execute_module(module_name='stat', module_args=dict(path=creates), task_vars=task_vars)
            stat = result.get('stat', None)
            if stat and stat.get('exists', False):
                result['skipped'] = True
                result['msg'] = "skipped, since %s exists" % creates
                return result

        if tmp is None:
            tmp = self._make_tmp_path()

        new_module_args = self._task.args.copy()
        
        if copy:
            result.update(self._copy(tmp,task_vars))
            if result.get('failed') or result.get('skipped'):
                if result.get('passback'):
                    del result['passback']
                return result    
        
            # how I got some values from _copy
            source = result['passback']['source']
            tmp_src = result['passback']['tmp_src']
            del result['passback']
            new_module_args['src'] = tmp_src
    
        # source may have been upated by _copy
        new_module_args['original_basename'] = os.path.basename(source)
    
        # execute the unarchive module and get archive type
        result.update(self._execute_module(module_args=new_module_args, task_vars=task_vars))
        if result.get('failed') or result.get('skipped'):
            return result
        if result.get('archive_type'):
            handler_for = {
                'TarArchive':     'untar',
                'TarBzipArchive': 'untar',
                'TarXzArchive':   'untar',
                'TgzArchive':     'untar',
                'ZipArchive':     'unzip',
            }
            if result['archive_type'] not in handler_for:
                result['failed'] = True
                result['msg'] = "No handler for archive type '%s'" % result['archive_type']
                return result
                
            new_module_args['archive_type'] = result['archive_type']
            result.update(self._execute_module(module_name=handler_for[result['archive_type']], module_args=new_module_args, task_vars=task_vars))
        else:
            result['failed'] = True
            result['msg'] = "Failed to determine archive type for '%s'" %  source
            return result
        
        return result
