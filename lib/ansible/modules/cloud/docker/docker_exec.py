#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'committer',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: docker_exec

short_description: run command in a docker containers

description:
  - Run commands in docker containers.
  - Does not support check mode

version_added: "2.3"

options:
  command:
    description:
      - Command to execute in the container.
    default: null
    required: true
  name:
    description:
      - Name of the container to run the command in.
      - The container name may be a name or a long or short container ID.
    required: true
extends_documentation_fragment:
    - docker

author:
    - "Bernie Schelberg (@bschelberg)"

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.7.0"
    - "Docker API >= 1.20"
'''

EXAMPLES = '''
- name: Run command in Docker container
  docker_exec:
    docker_host: docker.local:2375
    name: test-container
    command: ls
'''

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
