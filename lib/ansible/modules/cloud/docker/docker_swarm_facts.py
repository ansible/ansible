#!/usr/bin/python
#
# (c) 2019 Piotr Wojciechowski <piotr@it-playground.pl>
# (c) Thierry Bouvet (@tbouvet)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: docker_swarm_facts

short_description: Retrieves facts about Docker Swarm cluster.

description:
  - Retrieves facts about a Docker Swarm if run on Swarm Manager host.
  - Retrieves role of node on which it is run.

version_added: "2.8"

author:
    - Piotr Wojciechowski (@wojciechowskipiotr)
    - Thierry Bouvet (@tbouvet)

options:
  list:
    description:
      - Returns lists of components.
      - If C(nodes) the return list of registered nodes (the only supported option now).
      - If not present then return Swarm facts.
    choices:
        - nodes
    required: false
  output:
    description:
      - If C(short) and I(list) is C(nodes) then returns list of registered nodes names.
      - If C(long) and I(list) is C(nodes) then returns list as in output of `docker nodes ls`.
      - Ignored if I(list) is not present.
    choices:
      - short
      - long
    required: false
    default: short
extends_documentation_fragment:
    - docker

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
    - "Docker API >= 1.24"
'''

EXAMPLES = '''
- name: Get info on Docker Swarm
  docker_swarm_facts:
  register: result

- name: Get list of registered nodes
  docker_swarm_facts:
    list: nodes
  register: result

- name: Get extended list of registered nodes
  docker_swarm_facts:
    list: nodes
    output: long
  register: result
'''

RETURN = '''
node_role:
  description:
    - Information on role of docker host where M(docker_swarm_facts) is executed.
    - Will be C(Manager) if executed on Swarm manager.
    - Will be C(Worker) if executed on Swarm worker.
    - Will be C(Unknown) if executed on host not in Swarm or other error occurred.
  returned: always
  type: str
  example: "Manager"
swarm_facts:
  description:
    - Information about swarm including the JoinTokens.
    - Will be C(None) if module not executed on Swarm Manager.
    - Will be list if I(list) is specified
  returned: always
  type: complex
  contains:
      JoinTokens:
          description: Tokens to connect to the Swarm.
          returned: success
          type: complex
          contains:
              Worker:
                  description: Token to create a new I(worker) node.
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx
              Manager:
                  description: Token to create a new I(manager) node.
                  returned: success
                  type: str
                  example: SWMTKN-1--xxxxx

'''

import json

try:
    from docker.errors import APIError, NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_swarm import AnsibleDockerSwarmClient


def get_swarm_facts(client):
    if client.module.params['list'] == 'nodes':
        try:
            if client.module.params['output'] == 'long':
                data = client.get_all_nodes_list(output='long')
            else:
                data = client.get_all_nodes_list()
            json_str = json.dumps(data, ensure_ascii=False)
            nodes_info = json.loads(json_str)
            if nodes_info is None:
                return None, "Manager"
            return nodes_info, "Manager"
        except APIError:
            if client.check_if_swarm_worker(client):
                return None, "Worker"
            return None, "Unknown"
    if client.module.params['list'] == 'tasks':
        return None, None

    if client.module.params['list'] is None:
        try:
            data = client.inspect_swarm()
            json_str = json.dumps(data, ensure_ascii=False)
            swarm_info = json.loads(json_str)
            # return swarm_info, "Manager"
            return swarm_info, client.module.params['list']
        except APIError:
            if client.check_if_swarm_worker(client):
                return None, "Worker"
            return None, "Unknown"


def main():
    argument_spec = dict(
        list=dict(type='str', choices=['nodes']),
        output=dict(type='str', choices=['short', 'long'], default='short'),
    )

    client = AnsibleDockerSwarmClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.24',
    )

    swarm_facts, node_role = get_swarm_facts(client)

    client.module.exit_json(
        changed=False,
        swarm_facts=swarm_facts,
        node_role=node_role,
    )


if __name__ == '__main__':
    main()
