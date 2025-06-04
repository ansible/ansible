# Copyright 2012, Tim Bielawa <tbielawa@redhat.com>
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
from __future__ import annotations

import datetime
import time

from ansible.errors import AnsibleError, AnsiblePromptInterrupt, AnsiblePromptNoninteractive
from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):
    """ pauses execution for a length or time, or until input is received """

    BYPASS_HOST_LOOP = True

    def run(self, tmp=None, task_vars=None):
        """ run the pause action module """
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec={
                'echo': {'type': 'bool', 'default': True},
                'minutes': {'type': int},  # Don't break backwards compat, allow floats, by using int callable
                'seconds': {'type': int},  # Don't break backwards compat, allow floats, by using int callable
                'prompt': {'type': 'str'},
            },
            mutually_exclusive=(
                ('minutes', 'seconds'),
            ),
        )

        duration_unit = 'minutes'
        prompt = None
        seconds = None
        echo = new_module_args['echo']
        echo_prompt = ''
        result.update(dict(
            changed=False,
            rc=0,
            stderr='',
            stdout='',
            start=None,
            stop=None,
            delta=None,
            echo=echo
        ))

        # Add a note saying the output is hidden if echo is disabled
        if not echo:
            echo_prompt = ' (output is hidden)'

        if new_module_args['prompt']:
            prompt = "[%s]\n%s%s:" % (self._task.get_name().strip(), new_module_args['prompt'], echo_prompt)
        else:
            # If no custom prompt is specified, set a default prompt
            prompt = "[%s]\n%s%s:" % (self._task.get_name().strip(), 'Press enter to continue, Ctrl+C to interrupt', echo_prompt)

        if new_module_args['minutes'] is not None:
            seconds = new_module_args['minutes'] * 60
        elif new_module_args['seconds'] is not None:
            seconds = new_module_args['seconds']
            duration_unit = 'seconds'

        ########################################################################
        # Begin the hard work!

        start = time.time()
        result['start'] = to_text(datetime.datetime.now())
        result['user_input'] = b''

        default_input_complete = None
        if seconds is not None:
            if seconds < 1:
                seconds = 1

            # show the timer and control prompts
            display.display("Pausing for %d seconds%s" % (seconds, echo_prompt))

            # show the prompt specified in the task
            if new_module_args['prompt']:
                display.display("(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)\r")
            else:
                # corner case where enter does not continue, wait for timeout/interrupt only
                prompt = "(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)\r"

            # don't complete on LF/CR; we expect a timeout/interrupt and ignore user input when a pause duration is specified
            default_input_complete = tuple()

        # Only echo input if no timeout is specified
        echo = seconds is None and echo

        user_input = b''
        try:
            _user_input = display.prompt_until(prompt, private=not echo, seconds=seconds, complete_input=default_input_complete)
        except AnsiblePromptInterrupt:
            user_input = None
        except AnsiblePromptNoninteractive:
            if seconds is None:
                display.warning("Not waiting for response to prompt as stdin is not interactive")
            else:
                # wait specified duration
                time.sleep(seconds)
        else:
            if seconds is None:
                user_input = _user_input
        # user interrupt
        if user_input is None:
            prompt = "Press 'C' to continue the play or 'A' to abort \r"
            try:
                user_input = display.prompt_until(prompt, private=not echo, interrupt_input=(b'a',), complete_input=(b'c',))
            except AnsiblePromptInterrupt:
                raise AnsibleError('user requested abort!')

        duration = time.time() - start
        result['stop'] = to_text(datetime.datetime.now())
        result['delta'] = int(duration)

        if duration_unit == 'minutes':
            duration = round(duration / 60.0, 2)
        else:
            duration = round(duration, 2)
        result['stdout'] = "Paused for %s %s" % (duration, duration_unit)
        result['user_input'] = to_text(user_input, errors='surrogate_or_strict')
        return result
