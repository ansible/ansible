# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import time

from ansible.module_utils._text import to_text
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import ConnectionError

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class HttpApi:
    def __init__(self, connection):
        self.connection = connection
        self._become = False

    def send_request(self, data, **message_kwargs):
        data = to_list(data)
        if self._become:
            display.vvvv('firing event: on_become')
            data.insert(0, {"cmd": "enable", "input": self._become_pass})

        output = message_kwargs.get('output', 'text')
        request = request_builder(data, output)
        headers = {'Content-Type': 'application/json-rpc'}

        response = self.connection.send('/command-api', request, headers=headers, method='POST')
        response = json.loads(to_text(response.read()))
        results = handle_response(response)

        if self._become:
            results = results[1:]
        if len(results) == 1:
            results = results[0]

        return results

    def get_prompt(self):
        # Fake a prompt for @enable_mode
        if self._become:
            return '#'
        else:
            return '>'

    def set_become(self, play_context):
        self._become = play_context.become
        self._become_pass = getattr(play_context, 'become_pass') or ''

    # Imported from module_utils
    def edit_config(self, config, commit=False, replace=False):
        """Loads the configuration onto the remote devices

        If the device doesn't support configuration sessions, this will
        fallback to using configure() to load the commands.  If that happens,
        there will be no returned diff or session values
        """
        session = 'ansible_%s' % int(time.time())
        result = {'session': session}
        banner_cmd = None
        banner_input = []

        commands = ['configure session %s' % session]
        if replace:
            commands.append('rollback clean-config')

        for command in config:
            if command.startswith('banner'):
                banner_cmd = command
                banner_input = []
            elif banner_cmd:
                if command == 'EOF':
                    command = {'cmd': banner_cmd, 'input': '\n'.join(banner_input)}
                    banner_cmd = None
                    commands.append(command)
                else:
                    banner_input.append(command)
                    continue
            else:
                commands.append(command)

        try:
            response = self.send_request(commands)
        except Exception:
            commands = ['configure session %s' % session, 'abort']
            response = self.send_request(commands, output='text')
            raise

        commands = ['configure session %s' % session, 'show session-config diffs']
        if commit:
            commands.append('commit')
        else:
            commands.append('abort')

        response = self.send_request(commands, output='text')
        diff = response[1].strip()
        if diff:
            result['diff'] = diff

        return result

    def run_commands(self, commands, check_rc=True):
        """Runs list of commands on remote device and returns results
        """
        output = None
        queue = list()
        responses = list()

        def run_queue(queue, output):
            response = to_list(self.send_request(queue, output=output))
            if output == 'json':
                response = [json.loads(item) for item in response]
            return response

        for item in to_list(commands):
            cmd_output = None
            if isinstance(item, dict):
                command = item['command']
                if command.endswith('| json'):
                    command = command.replace('| json', '')
                    cmd_output = 'json'
                elif 'output' in item:
                    cmd_output = item['output']
            else:
                command = item
                cmd_output = 'json'

            if output and output != cmd_output:
                responses.extend(run_queue(queue, output))
                queue = list()

            output = cmd_output or 'json'
            queue.append(command)

        if queue:
            responses.extend(run_queue(queue, output))

        return responses

    def load_config(self, config, commit=False, replace=False):
        """Loads the configuration onto the remote devices

        If the device doesn't support configuration sessions, this will
        fallback to using configure() to load the commands.  If that happens,
        there will be no returned diff or session values
        """
        return self.edit_config(config, commit, replace)


def handle_response(response):
    if 'error' in response:
        error = response['error']

        error_text = []
        for data in error['data']:
            error_text.extend(data.get('errors', []))
        error_text = '\n'.join(error_text) or error['message']

        raise ConnectionError(error_text, code=error['code'])

    results = []
    for result in response['result']:
        if 'messages' in result:
            results.append(result['messages'][0])
        elif 'output' in result:
            results.append(result['output'].strip())
        else:
            results.append(json.dumps(result))

    return results


def request_builder(commands, output, reqid=None):
    params = dict(version=1, cmds=commands, format=output)
    return json.dumps(dict(jsonrpc='2.0', id=reqid, method='runCmds', params=params))
