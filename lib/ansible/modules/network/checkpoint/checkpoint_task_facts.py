#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_task(module, connection):
    task_id = module.params['task_id']

    payload = {'task-id': task_id}

    code, response = connection.send_request('/web_api/show-task', payload)

    return code, response


def main():
    argument_spec = dict(
        task_id=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_task(module, connection)
    if code == 200:
        module.exit_json(ansible_facts=dict(checkpoint_tasks=response))
    else:
        module.fail_json(msg='Checkpoint device returned error {} with message {}'.format(code, response))

if __name__ == '__main__':
    main()
