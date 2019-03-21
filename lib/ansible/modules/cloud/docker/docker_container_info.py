#!/usr/bin/python
#
# Copyright 2016 Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker_container_info

short_description: Retrieves facts about docker container

description:
  - Retrieves facts about a docker container.
  - Essentially returns the output of C(docker inspect <name>), similar to what M(docker_container)
    returns for a non-absent container.

version_added: "2.8"

options:
  name:
    description:
      - The name of the container to inspect.
      - When identifying an existing container name may be a name or a long or short container ID.
    type: str
    required: yes
extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

author:
  - "Felix Fontein (@felixfontein)"

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.8.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
  - "Docker API >= 1.20"
'''

EXAMPLES = '''
- name: Get infos on container
  docker_container_info:
    name: mydata
  register: result

- name: Does container exist?
  debug:
    msg: "The container {{ 'exists' if result.exists else 'does not exist' }}"

- name: Print information about container
  debug:
    var: result.container
  when: result.exists
'''

RETURN = '''
exists:
    description:
      - Returns whether the container exists.
    type: bool
    returned: always
    sample: true
container:
    description:
      - Facts representing the current state of the container. Matches the docker inspection output.
      - Will be C(None) if container does not exist.
    returned: always
    type: dict
    sample: '{
        "AppArmorProfile": "",
        "Args": [],
        "Config": {
            "AttachStderr": false,
            "AttachStdin": false,
            "AttachStdout": false,
            "Cmd": [
                "/usr/bin/supervisord"
            ],
            "Domainname": "",
            "Entrypoint": null,
            "Env": [
                "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
            ],
            "ExposedPorts": {
                "443/tcp": {},
                "80/tcp": {}
            },
            "Hostname": "8e47bf643eb9",
            "Image": "lnmp_nginx:v1",
            "Labels": {},
            "OnBuild": null,
            "OpenStdin": false,
            "StdinOnce": false,
            "Tty": false,
            "User": "",
            "Volumes": {
                "/tmp/lnmp/nginx-sites/logs/": {}
            },
            ...
    }'
'''

from ansible.module_utils.docker.common import AnsibleDockerClient


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_api_version='1.20',
    )

    container = client.get_container(client.module.params['name'])

    client.module.exit_json(
        changed=False,
        exists=(True if container else False),
        container=container,
    )


if __name__ == '__main__':
    main()
