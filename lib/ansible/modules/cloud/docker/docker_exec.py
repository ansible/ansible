#!/usr/bin/python

from ansible.module_utils.docker_common import AnsibleDockerClient

def main():
    argument_spec = dict(
        command=dict(type='str'),
        name=dict(type='str', required=True),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    container = client.get_container(client.module.params['name'])
    create_result = client.exec_create(container, client.module.params['command'])
    start_result = client.exec_start(create_result)

    client.module.exit_json(changed=True, result=start_result)

if __name__ == '__main__':
    main()
