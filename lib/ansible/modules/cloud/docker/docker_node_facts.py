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
module: docker_node_facts

short_description: Retrieves facts about docker swarm node from Swarm Manager

description:
  - Retrieves facts about a docker node.
  - Essentially returns the output of C(docker node inspect <name>).
  - Must be executed on a host running as Swarm Manager, otherwise the module will fail.

version_added: "2.8"

options:
  name:
    description:
      - The name of the node to inspect.
      - When identifying an existing node name may either the hostname of the node (as registered in Swarm) or node ID.
    required: true
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
    - "Docker API >= 1.24"
'''

EXAMPLES = '''
- name: Get info on node
  docker_node_facts:
    name: mynode
  register: result

'''

RETURN = '''
exists:
    description:
      - Returns whether the node exists in docker swarm cluster.
    type: bool
    returned: always
    sample: true
node_facts:
    description:
      - Facts representing the current state of the node. Matches the C(docker node inspect) output.
      - Will be C(None) if node does not exist.
    returned: always
    type: dict

'''

from ansible.module_utils.docker_common import AnsibleDockerClient
from ansible.module_utils._text import to_native

try:
    from docker.errors import APIError, NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass


def get_node_facts(client, name):
    try:
        return client.inspect_node(name)
    except NotFound:
        return None
    except APIError as exc:
        if exc.status_code == 503:
            client.fail(msg="Cannot inspect node: To inspect node execute module on Swarm Manager")
        client.fail(msg="Error while reading from Swarm manager: %s" % to_native(exc))
    except Exception as exc:
        client.module.fail_json(msg="Error inspecting swarm node: %s" % exc)


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.10.0',
        min_docker_api_version='1.24',
    )

    node = get_node_facts(client, client.module.params['name'])

    client.module.exit_json(
        changed=False,
        exists=(True if node else False),
        node_facts=node,
    )


if __name__ == '__main__':
    main()
