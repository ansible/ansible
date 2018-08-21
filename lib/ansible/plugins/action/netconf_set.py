#
# (c) 2018, Red Hat, Inc.
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

import os
import re
import time
import glob

from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils._text import to_text, to_bytes
from ansible.module_utils.six.moves.urllib.parse import urlsplit

PRIVATE_KEYS_RE = re.compile('__.+__')


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if self._task.args.get('backup') and result.get('__backup__'):
            # User requested backup and no error occurred in module.
            # NOTE: If there is a parameter error, _backup key may not be in results.
            filepath = self._write_backup(task_vars['inventory_hostname'],
                                          result['__backup__'])

            result['backup_path'] = filepath

        # strip out any keys that have two leading and two trailing
        # underscore characters
        for key in list(result.keys()):
            if PRIVATE_KEYS_RE.match(key):
                del result[key]

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
        with open(filename, 'wb') as f:
            f.write(to_bytes(to_text(contents, encoding='latin-1'), encoding='utf-8'))
        return filename
