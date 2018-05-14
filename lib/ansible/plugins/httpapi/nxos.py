# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.module_utils._text import to_text
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import to_list

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class HttpApi:
    def __init__(self, connection):
        self.connection = connection

    def send_request(self, data, **message_kwargs):
        if 'become' in message_kwargs:
            display.vvvv('firing event: on_become')
            # TODO ??? self._terminal.on_become(passwd=auth_pass)

        output = message_kwargs.get('output', 'text')
        request = request_builder(data, output)
        headers = {'Content-Type': 'application/json'}

        response = self.connection.send('/ins', request, headers=headers, method='POST')
        response = json.loads(to_text(response.read()))
        return handle_response(response)

    # Migrated from module_utils
    def edit_config(self, command):
        responses = self.send_request(command, output='config')
        return json.dumps(responses)

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
            if item['command'].endswith('| json'):
                item['command'] = item['command'].rsplit('|', 1)[0]
                item['output'] = 'json'

            if output and output != item['output']:
                responses.extend(run_queue(queue, output))
                queue = list()

            output = item['output'] or 'json'
            queue.append(item['command'])

        if queue:
            responses.extend(run_queue(queue, output))

        return responses


def handle_response(response):
    results = []

    if response['ins_api'].get('outputs'):
        for output in to_list(response['ins_api']['outputs']['output']):
            if output['code'] != '200':
                raise ConnectionError('%s: %s' % (output['input'], output['msg']))
            elif 'body' in output:
                result = output['body']
                if isinstance(result, dict):
                    result = json.dumps(result)

                results.append(result.strip())

    if len(results) == 1:
        return results[0]
    return results


def request_builder(commands, output, version='1.0', chunk='0', sid=None):
    """Encodes a NXAPI JSON request message
    """
    output_to_command_type = {
        'text': 'cli_show_ascii',
        'json': 'cli_show',
        'bash': 'bash',
        'config': 'cli_conf'
    }

    maybe_output = commands[0].split('|')[-1].strip()
    if maybe_output in output_to_command_type:
        command_type = output_to_command_type[maybe_output]
        commands = [command.split('|')[0].strip() for command in commands]
    else:
        try:
            command_type = output_to_command_type[output]
        except KeyError:
            msg = 'invalid format, received %s, expected one of %s' % \
                (output, ','.join(output_to_command_type.keys()))
            raise ConnectionError(msg)

    if isinstance(commands, (list, set, tuple)):
        commands = ' ;'.join(commands)

    msg = {
        'version': version,
        'type': command_type,
        'chunk': chunk,
        'sid': sid,
        'input': commands,
        'output_format': 'json'
    }
    return json.dumps(dict(ins_api=msg))
