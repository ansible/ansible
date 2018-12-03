#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_access_rule(module, connection):
    name = module.params['name']
    uid = module.params['uid']
    layer = module.params['layer']

    if uid:
        payload = {'uid': uid, 'layer': layer}
    elif name:
        payload = {'name': name, 'layer': layer}

    res = connection.send_request('/web_api/show-access-rule', payload)

    return res


def main():
    argument_spec = dict(
        name=dict(type='str'),
        uid=dict(type='str'),
        layer=dict(type='str', required=True),
        state=dict(type='str', default='present')
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_access_rule(module, connection)

    if code >= 500:
        module.fail_json(msg='Checkpoint device returned error {} with message {}'.format(code, response))

    if module.params['state'] == 'present':
        if code == 200:
            # Handle update
        elif code = 404:
            # Handle creation
    else:
        if code == 200:
            # Handle deletion
        elif code: 404:
            pass

if __name__ == '__main__':
    main()
