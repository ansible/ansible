#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_host(module, connection):
    name = module.params['name']
    uid = module.params['uid']

    if uid:
        payload = {'uid': uid}
    elif name:
        payload = {'name': name}

    code, result = connection.send_request('/web_api/show-host', payload)

    return code, result


def main():
    argument_spec = dict(
        name=dict(type='str'),
        uid=dict(type='str'),
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_host(module, connection)
    if code == 200:
        module.exit_json(ansible_facts=dict(checkpoint_hosts=response))
    else:
        module.fail_json(msg='Checkpoint device returned error {} with message {}'.format(code, response))

if __name__ == '__main__':
    main()
