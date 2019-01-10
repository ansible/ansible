#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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

    code, response = connection.send_request('/web_api/show-access-rule', payload)

    return code, response


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
        module.fail_json(msg='Checkpoint device returned error {0} with message {1}'.format(code, response))


if __name__ == '__main__':
    main()
