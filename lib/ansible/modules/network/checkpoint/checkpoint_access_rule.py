#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.six.moves.urllib.error import HTTPError
import json


def get_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']

    payload = {'name': name, 'layer': layer}

    res = connection.send_request('/web_api/show-access-rule', payload)

    return res

def create_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']
    position = module.params['position']
    source = module.params['source']
    destination = module.params['destination']
    action = module.params['action']

    payload = {'name': name,
               'layer': layer,
               'position': position,
               'source': source,
               'destination': destination,
               'action': action}

    res = connection.send_request('/web_api/add-access-rule', payload)

    return res

def delete_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']

    payload = {'name': name,
               'layer': layer,
              }

    res = connection.send_request('/web_api/delete-access-rule', payload)

    return res

def publish(module, connection):
    res = connection.send_request('/web_api/publish', None)

def install_policy(module, connection):
    payload = {'policy-package': 'standard'}
    res = connection.send_request('/web_api/install-policy', payload)

def main():
    argument_spec = dict(
        name=dict(type='str'),
        layer=dict(type='str', required=True),
        position=dict(type='str', required=True),
        source=dict(type='str'),
        destination=dict(type='str'),
        action=dict(type='str'),
        state=dict(type='str', default='present')
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_access_rule(module, connection)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            # Handle update
            result['changed'] = False
            result['checkpoint_access_rules'] = response
        else:
            response = create_access_rule(module, connection)
            publish(module, connection)
            install_policy(module, connection)
            result['changed'] = True
            result['checkpoint_access_rules'] = response

    else:
        if code == 200:
            # Handle deletion
            response = delete_access_rule(module, connection)
            publish(module, connection)
            install_policy(module, connection)
            result['changed'] = True
            result['checkpoint_access_rules'] = response
        elif code == 404:
            result['changed'] = False
            result['checkpoint_access_rules'] = response

    module.exit_json(**result)
if __name__ == '__main__':
    main()
