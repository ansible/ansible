#
# Copyright 2015 Peter Sprygada <psprygada@ansible.com>
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import sys
import os
import time
import glob
import urlparse

from ansible.plugins.action import ActionBase
from ansible.utils.unicode import to_unicode


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False

        src = self._task.args.get('src')

        if src:
            if src.endswith('.xml'):
                fmt = 'xml'
            elif src.endswith('.set'):
                fmt = 'set'
            else:
                fmt = 'text'

            if self._task.args.get('format') is None:
                self._task.args['format'] = fmt

        try:
            self._handle_source()
        except ValueError as exc:
            return dict(failed=True, msg=exc.message)

        if self._task.args.get('comment') is None:
            self._task.args['comment'] = self._task.name

        result.update(self._execute_module(module_name=self._task.action,
            module_args=self._task.args, task_vars=task_vars))

        if self._task.args.get('backup') and result.get('_backup'):
            # User requested backup and no error occurred in module.
            # NOTE: If there is a parameter error, _backup key may not be in results.
            self._write_backup(task_vars['inventory_hostname'], result['_backup'])

        if '_backup' in result:
            del result['_backup']

        return result

    def _get_working_path(self):
        cwd = self._loader.get_basedir()
        if self._task._role is not None:
            cwd = self._task._role._role_path
        return cwd

    def _write_backup(self, host, contents):
        backup_path = self._get_working_path() + '/backup'
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)
        for fn in glob.glob('%s/%s*' % (backup_path, host)):
            os.remove(fn)
        tstamp = time.strftime("%Y-%m-%d@%H:%M:%S", time.localtime(time.time()))
        filename = '%s/%s_config.%s' % (backup_path, host, tstamp)
        open(filename, 'w').write(contents)

    def _handle_source(self):
        src = self._task.args.get('src')
        working_path = self._get_working_path()

        if os.path.isabs(src) or urlparse.urlsplit('src').scheme:
            source = src
        else:
            source = self._loader.path_dwim_relative(working_path, 'files', src)
            if not source:
                source = self._loader.path_dwim_relative(working_path, src)

        if not os.path.exists(source):
            raise ValueError('Unable to load source file')

        try:
            with open(source, 'r') as f:
                template_data = to_unicode(f.read())
        except IOError:
            return dict(failed=True, msg='unable to load src file')

        self._task.args['src'] = self._templar.template(template_data)



