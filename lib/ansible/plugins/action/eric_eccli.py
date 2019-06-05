#
# Copyright (c) 2019 Ericsson AB.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action.normal import ActionModule as _ActionModule


class ActionModule(_ActionModule):

    def run(self, tmp=None, task_vars=None):
        if self._play_context.connection != 'network_cli':
            return {'failed': True, 'msg': 'Connection type %s is not valid for cli_config module' % self._play_context.connection}

        return super(ActionModule, self).run(task_vars=task_vars)
