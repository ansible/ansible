#
# (c) 2017, Red Hat, Inc.
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

import re

from ansible.plugins.action.aruba import ActionModule as _ActionModule
from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.backup import write_backup, handle_template

PRIVATE_KEYS_RE = re.compile('__.+__')


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):

        if self._task.args.get('src'):
            try:
                self._task.args['src'] = handle_template(self)
            except ValueError as exc:
                return dict(failed=True, msg=to_text(exc))

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if self._task.args.get('backup') and result.get('__backup__'):
            # User requested backup and no error occurred in module.
            # NOTE: If there is a parameter error, _backup key may not be in results.
            filepath = write_backup(self, task_vars['inventory_hostname'], result['__backup__'])
            result['backup_path'] = filepath

        # strip out any keys that have two leading and two trailing
        # underscore characters
        for key in list(result):
            if PRIVATE_KEYS_RE.match(key):
                del result[key]

        return result
