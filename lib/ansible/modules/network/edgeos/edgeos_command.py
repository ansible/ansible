#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
"""

EXAMPLES = """
"""

RETURN = """
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils._text import to_text


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        command=dict(required=True),
        prompt=dict(),
        answer=dict()
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    command = module.params['command']
    prompt = module.params['prompt']
    answer = module.params['answer']

    if module.check_mode and not command.startswith('show'):
        module.warn('only `show` commands are supported when using check mode,\
                     skipping %s' % command)

    try:
        connection = Connection(module._socket_path)
        response = connection.get(command, prompt, answer)
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc))

    result.update({'stdout': response})

    module.exit_json(**result)


if __name__ == '__main__':
    main()
