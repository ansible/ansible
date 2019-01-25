#!/usr/bin/python
#
# (c) 2019 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker_host_facts

short_description: Retrieves facts about docker host and lists of objects of the services

description:
  - Retrieves facts about a docker host.
  - Essentially returns the output of C(docker system info).
  - Returns lists of objects names for the services - images, networks, volumes, containers.
  - Returns disk usage information.
  - The output differs depending on API version available on docker host.
  - Must be executed on a host running a Docker, otherwise the module will fail.

version_added: "2.8"

options:
extends_documentation_fragment:
    - docker

author:
    - Piotr Wojciechowski (@wojciechowskipiotr)

requirements:
    - "python >= 2.6"
    - "docker-py >= 1.10.0"
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
- name: Get info on docker host
  docker_host_facts:
  register: result

'''

RETURN = '''
exists:
    description:
      - Returns whether the node exists in docker swarm cluster.
    type: bool
    returned: always
    sample: true
docker_host_facts:
    description:
      - Facts representing the current state of the docker host. Matches the C(docker system info) output.
    returned: always
    type: dict

'''

from ansible.module_utils.docker_common import AnsibleDockerClient, DockerBaseClass
from ansible.module_utils._text import to_native

try:
    from docker.errors import APIError, NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


class DockerHostManager(DockerBaseClass):

    def __init__(self, client, results):

        super(DockerHostManager, self).__init__()

        self.client = client
        self.results = results

        self.results['docker_host_facts'] = self.get_docker_host_facts()

    def get_docker_host_facts(self):
        try:
            return self.client.info()
        except Exception as exc:
            self.client.fail_json(msg="Error inspecting docker host: %s" % exc)


def main():
    argument_spec = dict(
        services=dict(type='list', elements='str'),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.21',
    )

    results = dict(
        changed=False,
        docker_host_facts=[]
    )

    DockerHostManager(client, results)
    client.module.exit_json(**results)


if __name__ == '__main__':
    main()
