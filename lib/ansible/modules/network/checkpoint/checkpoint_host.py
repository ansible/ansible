#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import publish, install_policy
import json


def get_host(module, connection):
    name = module.params['name']

    payload = {'name': name}

    code, response = connection.send_request('/web_api/show-host', payload)

    return code, response

def create_host(module, connection):
    name = module.params['name']
    ip_address = module.params['ip_address']

    payload = {'name': name,
               'ip-address': ip_address}

    code, response = connection.send_request('/web_api/add-host', payload)

    return code, response

def update_host(module, connection):
    name = module.params['name']
    ip_address = module.params['ip_address']

    payload = {'name': name,
               'ip-address': ip_address}

    code, response = connection.send_request('/web_api/set-host', payload)

    return code, response

def delete_host(module, connection):
    name = module.params['name']
    ip_address = module.params['ip_address']

    payload = {'name': name,
              }

    code, response = connection.send_request('/web_api/delete-host', payload)

    return code, response

def needs_update(module, host):
    res = False

    if  module.params['ip_address'] != host['ipv4-address']:
        res = True
    return res

def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        ip_address=dict(type='str', required=True),
        state=dict(type='str', default='present')
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = get_host(module, connection)
    result = {'changed': False}

    if module.params['state'] == 'present':
        if code == 200:
            if needs_update(module, response):
                code, response = update_host(module, connection)
                publish(module, connection)
                install_policy(module, connection)
                result['changed'] = True
                result['checkpoint_hosts'] = response
            else:
                pass
        else:
            code, response = create_host(module, connection)
            publish(module, connection)
            install_policy(module, connection)
            result['changed'] = True
            result['checkpoint_hosts'] = response
    else:
        if code == 200:
            # Handle deletion
            code, response = delete_host(module, connection)
            publish(module, connection)
            install_policy(module, connection)
            result['changed'] = True
            pass
        elif code == 404:
            pass

    module.exit_json(**result)
if __name__ == '__main__':
    main()
