#
# Copyright 2018 Red Hat Inc.
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

from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils.network.common.backup import write_backup


PRIVATE_KEYS_RE = re.compile('__.+__')


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        if self._play_context.connection != 'network_cli':
            return {'failed': True, 'msg': 'Connection type %s is not valid for cli_config module' % self._play_context.connection}

        result = super(ActionModule, self).run(task_vars=task_vars)

        if self._task.args.get('backup') and result.get('__backup__'):
            # User requested backup and no error occurred in module.
            # NOTE: If there is a parameter error, _backup key may not be in results.
            filepath = write_backup(self, task_vars['inventory_hostname'], result['__backup__'])
            result['backup_path'] = filepath

        # strip out any keys that have two leading and two trailing
        # underscore characters
        for key in list(result.keys()):
            if PRIVATE_KEYS_RE.match(key):
                del result[key]

        return result
