#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import publish, install_policy
import json


def get_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']

    payload = {'name': name, 'layer': layer}

    code, response = connection.send_request('/web_api/show-access-rule', payload)

    return code, response

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

    code, response = connection.send_request('/web_api/add-access-rule', payload)

    return code, response

def update_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']
    position = module.params['position']
    source = module.params['source']
    destination = module.params['destination']
    action = module.params['action']
    enabled = module.params['enabled']

    payload = {'name': name,
               'layer': layer,
               'position': position,
               'source': source,
               'destination': destination,
               'action': action,
               'enabled': enabled}

    code, response = connection.send_request('/web_api/set-access-rule', payload)

    return code, response

def delete_access_rule(module, connection):
    name = module.params['name']
    layer = module.params['layer']

    payload = {'name': name,
               'layer': layer,
              }

    code, response = connection.send_request('/web_api/delete-access-rule', payload)

    return code, response

def needs_update(module, access_rule):
    res = False

    if module.params['source'] != access_rule['source'][0]['name']:
        res = True
    if module.params['destination'] != access_rule['destination'][0]['name']:
        res = True
    if module.params['action'] != access_rule['action']['name']:
        res = True
    if module.params['enabled'] != access_rule['enabled']:
        res = True

    return res

def main():
    argument_spec = dict(
        name=dict(type='str'),
        layer=dict(type='str', required=True),
        position=dict(type='str', required=True),
        source=dict(type='str'),
        destination=dict(type='str'),
        action=dict(type='str'),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present')
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_access_rule(module, connection)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if needs_update(module, response):
                code, response = update_access_rule(module, connection)
                publish(module, connection)
                install_policy(module, connection)
                result['changed'] = True
                result['checkpoint_access_rules'] = response
            else:
                pass
        else:
            code, response = create_access_rule(module, connection)
            publish(module, connection)
            install_policy(module, connection)
            result['changed'] = True
            result['checkpoint_access_rules'] = response
    else:
        if code == 200:
            # Handle deletion
            code, response = delete_access_rule(module, connection)
            publish(module, connection)
            install_policy(module, connection)
            result['changed'] = True
            pass
        elif code == 404:
            pass

    module.exit_json(**result)
if __name__ == '__main__':
    main()
