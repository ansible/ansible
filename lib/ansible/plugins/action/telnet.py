# (c) 2017, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import telnetlib
from time import sleep

from ansible.module_utils._text import to_native
from ansible.module_utils.six import text_type
from ansible.plugins.action import ActionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):

        if self._task.environment and any(self._task.environment):
            self._display.warning('The telnet task does not support the environment keyword')

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if self._play_context.check_mode:
            # in --check mode, always skip this module execution
            result['skipped'] = True
            result['msg'] = 'The telnet task does not support check mode'
        else:
            result['changed'] = True
            result['failed'] = False

            host = self._task.args.get('host', self._play_context.remote_addr)
            user = self._task.args.get('user', self._play_context.remote_user)
            password = self._task.args.get('password', self._play_context.password)

            # FIXME, default to play_context?
            port = self._task.args.get('port', '23')
            timeout = self._task.args.get('timeout', 120)
            pause = self._task.args.get('pause', 1)

            send_newline = self._task.args.get('send_newline', False)

            login_prompt = self._task.args.get('login_prompt', "login: ")
            password_prompt = self._task.args.get('password_prompt', "Password: ")
            prompts = self._task.args.get('prompts', ["$ "])
            commands = self._task.args.get('command') or self._task.args.get('commands')

            if isinstance(commands, text_type):
                commands = commands.split(',')

            if isinstance(commands, list) and commands:

                tn = telnetlib.Telnet(host, port, timeout)

                output = []
                try:
                    if send_newline:
                        tn.write('\n')

                    tn.read_until(login_prompt)
                    tn.write('%s\n' % to_native(user))

                    if password:
                        tn.read_until(password_prompt)
                        tn.write('%s\n' % to_native(password))

                    tn.expect(prompts)

                    for cmd in commands:
                        display.vvvvv('>>> %s' % cmd)
                        tn.write('%s\n' % to_native(cmd))
                        index, match, out = tn.expect(prompts)
                        display.vvvvv('<<< %s' % cmd)
                        output.append(out)
                        sleep(pause)

                    tn.write("exit\n")

                except EOFError as e:
                    result['failed'] = True
                    result['msg'] = 'Telnet action failed: %s' % to_native(e)
                finally:
                    if tn:
                        tn.close()
                    result['output'] = output
            else:
                result['failed'] = True
                result['msg'] = 'Telnet requires a command to execute'

        return result
