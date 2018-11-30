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
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_access_rule(module, connection)
    if code == 200:
        module.exit_json(ansible_facts=dict(checkpoint_access_rules=response))
    else:
        module.fail_json(msg='Checkpoint device returned error {} with message {}'.format(code, response))

if __name__ == '__main__':
    main()
