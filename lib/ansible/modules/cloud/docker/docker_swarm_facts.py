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
module: docker_swarm_facts

short_description: Retrieves facts about docker swarm cluster from swarm manager

description:
  - Retrieves facts about a docker swarm.

version_added: "2.8"

extends_documentation_fragment:
    - docker

author:
    - Piotr Wojciechowski (@wojciechowskipiotr)
    - Thierry Bouvet (@tbouvet)


requirements:
    - python >= 2.7
    - "docker >= 2.6.0"
    - "Please note that the L(docker-py,https://pypi.org/project/docker-py/) Python
       module has been superseded by L(docker,https://pypi.org/project/docker/)
       (see L(here,https://github.com/docker/docker-py/issues/1310) for details).
       Version 2.1.0 or newer is only available with the C(docker) module."
    - Docker API >= 1.25
'''

EXAMPLES = '''
- name: Get info on node
  docker_swarm_facts:
  register: result

'''

RETURN = '''
swarm_facts:
  description: Information about swarm including the JoinTokens
  returned: success
  type: complex
  contains:
      JoinTokens:
          description: Tokens to connect to the Swarm.
          returned: success
          type: complex
          contains:
              Worker:
                  description: Token to create a new I(worker) node
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx
              Manager:
                  description: Token to create a new I(manager) node
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx

'''

from ansible.module_utils.docker_common import AnsibleDockerClient
import json

try:
    from docker.errors import APIError, NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


def get_node_facts(client):
    try:
        data = client.inspect_swarm()
        json_str = json.dumps(data, ensure_ascii=False)
        swarm_info = json.loads(json_str)
        return swarm_info
    except APIError:
        return


def main():
    option_minimal_versions = dict(
        signing_ca_cert=dict(docker_api_version='1.30'),
        signing_ca_key=dict(docker_api_version='1.30'),
        ca_force_rotate=dict(docker_api_version='1.30'),
    )

    client = AnsibleDockerClient(
        argument_spec=None,
        supports_check_mode=True,
        min_docker_version='2.6.0',
        min_docker_api_version='1.25',
        option_minimal_versions=option_minimal_versions,
    )

    swarm_facts = get_node_facts(client)

    client.module.exit_json(
        changed=False,
        swarm_facts=swarm_facts,
    )


if __name__ == '__main__':
    main()
