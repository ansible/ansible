# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        self._supports_async = True
        results = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        # Command module has a special config option to turn off the command nanny warnings
        if 'warn' not in self._task.args:
            self._task.args['warn'] = C.COMMAND_WARNINGS

        # Suggest using reboot module when shutdown and reboot commands are found.
        # Do this here rather than in the module because rebooting the system causes
        # the module to fail before the warning makes it back to the control node.
        if self._task.args['warn']:
            command = None
            command_re = re.compile(r'(?:^|(?:/\S+/)+|(?:(?:&&|;)\s*))(shutdown|reboot)\b')
            commandline = self._task._attributes['args'].get('_raw_params', None)
            if commandline:
                command_match = command_re.search(commandline)
                if command_match:
                    command = command_match.groups()[0]

                if command:
                    disable_suffix = "If you need to use '{cmd}' because reboot is insufficient you can add" \
                                     " 'warn: false' to this command task or set 'command_warnings=False' in" \
                                     " ansible.cfg to get rid of this message."
                    msg = "Consider using the reboot module rather than running '{cmd}'. " + disable_suffix
                    display.warning(msg.format(cmd=command))

        wrap_async = self._task.async_val and not self._connection.has_native_async
        results = merge_hash(results, self._execute_module(task_vars=task_vars, wrap_async=wrap_async))

        if not wrap_async:
            # remove a temporary path we created
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return results
