#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.checkpoint.checkpoint import publish, install_policy
import json


def run_script(module, connection):
    script_name = module.params['script_name']
    script = module.params['script']
    targets = module.params['targets']

    payload = {'script-name': script_name,
               'script': script,
               'targets': targets} 

    code, response = connection.send_request('/web_api/run-script', payload)

    return code, response

def main():
    argument_spec = dict(
        script_name=dict(type='str', required=True),
        script=dict(type='str', required=True),
        targets=dict(type='list', required=True)
    )

    module = AnsibleModule(argument_spec=argument_spec)
    connection = Connection(module._socket_path)
    code, response = run_script(module, connection)
    result = {'changed': True}

    if code == 200:
        result['checkpoint_run_script'] = response
    else:
        module.fail_json(msg='Checkpoint device returned error {} with message {}'.format(code, response))

    module.exit_json(**result)
if __name__ == '__main__':
    main()
