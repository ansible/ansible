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
module: docker_network_facts

short_description: Retrieves facts about docker network

description:
  - Retrieves facts about a docker network.
  - Essentially returns the output of C(docker network inspect <name>), similar to what M(docker_network)
    returns for a non-absent network.

version_added: "2.8"

options:
  name:
    description:
      - The name of the network to inspect.
      - When identifying an existing network name may be a name or a long or short network ID.
    required: true
extends_documentation_fragment:
    - docker

author:
    - "Dave Bendit (@DBendit)"

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.8.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       For Python 2.6, C(docker-py) must be used. Otherwise, it is recommended to
       install the C(docker) Python module. Note that both modules should I(not)
       be installed at the same time. Also note that when both modules are installed
       and one of them is uninstalled, the other might no longer function and a
       reinstall of it is required."
    - "Docker API >= 1.21"
'''

EXAMPLES = '''
- name: Get infos on network
  docker_network_facts:
    name: mydata
  register: result

- name: Does network exist?
  debug:
    msg: "The network {{ 'exists' if result.exists else 'does not exist' }}"

- name: Print information about network
  debug:
    var: result.docker_network
  when: result.exists
'''

RETURN = '''
exists:
    description:
      - Returns whether the network exists.
    type: bool
    returned: always
    sample: true
docker_network:
    description:
      - Facts representing the current state of the network. Matches the docker inspection output.
      - Will be C(None) if network does not exist.
    returned: always
    type: dict
    sample: '{
        "Attachable": false,
        "ConfigFrom": {
            "Network": ""
        },
        "ConfigOnly": false,
        "Containers": {},
        "Created": "2018-12-07T01:47:51.250835114-06:00",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Config": [
                {
                    "Gateway": "192.168.96.1",
                    "Subnet": "192.168.96.0/20"
                }
            ],
            "Driver": "default",
            "Options": null
        },
        "Id": "0856968545f22026c41c2c7c3d448319d3b4a6a03a40b148b3ac4031696d1c0a",
        "Ingress": false,
        "Internal": false,
        "Labels": {},
        "Name": "ansible-test-f2700bba",
        "Options": {},
        "Scope": "local"
    }'
'''

from ansible.module_utils.docker_common import AnsibleDockerClient


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_api_version='1.21',
    )

    network = client.get_network(client.module.params['name'])

    client.module.exit_json(
        changed=False,
        exists=(True if network else False),
        docker_network=network,
    )


if __name__ == '__main__':
    main()
