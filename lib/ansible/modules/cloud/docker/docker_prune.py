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
module: docker_prune

short_description: Allows to prune various docker objects

description:
  - Allows to run C(docker container prune), C(docker image prune), C(docker network prune)
    and C(docker volume prune) via the Docker API.

version_added: "2.8"

options:
  containers:
    description:
      - Whether to prune containers.
    type: bool
    default: no
  containers_filters:
    description:
      - A dictionary of filter values used for selecting containers to delete.
      - "For example, C(until: 24h)."
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/container_prune/#filtering)
        for more information on possible filters.
    type: dict
  images:
    description:
      - Whether to prune images.
    type: bool
    default: no
  images_filters:
    description:
      - A dictionary of filter values used for selecting images to delete.
      - "For example, C(dangling: true)."
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/image_prune/#filtering)
        for more information on possible filters.
    type: dict
  networks:
    description:
      - Whether to prune networks.
    type: bool
    default: no
  networks_filters:
    description:
      - A dictionary of filter values used for selecting networks to delete.
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/network_prune/#filtering)
        for more information on possible filters.
    type: dict
  volumes:
    description:
      - Whether to prune volumes.
    type: bool
    default: no
  volumes_filters:
    description:
      - A dictionary of filter values used for selecting volumes to delete.
      - See L(the docker documentation,https://docs.docker.com/engine/reference/commandline/volume_prune/#filtering)
        for more information on possible filters.
    type: dict
  builder_cache:
    description:
      - Whether to prune the builder cache.
      - Requires version 3.3.0 of the Docker SDK for Python or newer.
    type: bool
    default: no

extends_documentation_fragment:
  - docker
  - docker.docker_py_2_documentation

author:
  - "Felix Fontein (@felixfontein)"

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 2.1.0"
  - "Docker API >= 1.25"
'''

EXAMPLES = '''
- name: Prune containers older than 24h
  docker_prune:
    containers: yes
    containers_filters:
      # only consider containers created more than 24 hours ago
      until: 24h

- name: Prune everything
  docker_prune:
    containers: yes
    images: yes
    networks: yes
    volumes: yes
    builder_cache: yes

- name: Prune everything (including non-dangling images)
  docker_prune:
    containers: yes
    images: yes
    images_filters:
      dangling: false
    networks: yes
    volumes: yes
    builder_cache: yes
'''

RETURN = '''
# containers
containers:
    description:
      - List of IDs of deleted containers.
    returned: I(containers) is C(true)
    type: list
    elements: str
    sample: '[]'
containers_space_reclaimed:
    description:
      - Amount of reclaimed disk space from container pruning in bytes.
    returned: I(containers) is C(true)
    type: int
    sample: '0'

# images
images:
    description:
      - List of IDs of deleted images.
    returned: I(images) is C(true)
    type: list
    elements: str
    sample: '[]'
images_space_reclaimed:
    description:
      - Amount of reclaimed disk space from image pruning in bytes.
    returned: I(images) is C(true)
    type: int
    sample: '0'

# networks
networks:
    description:
      - List of IDs of deleted networks.
    returned: I(networks) is C(true)
    type: list
    elements: str
    sample: '[]'

# volumes
volumes:
    description:
      - List of IDs of deleted volumes.
    returned: I(volumes) is C(true)
    type: list
    elements: str
    sample: '[]'
volumes_space_reclaimed:
    description:
      - Amount of reclaimed disk space from volumes pruning in bytes.
    returned: I(volumes) is C(true)
    type: int
    sample: '0'

# builder_cache
builder_cache_space_reclaimed:
    description:
      - Amount of reclaimed disk space from builder cache pruning in bytes.
    returned: I(builder_cache) is C(true)
    type: int
    sample: '0'
'''

import traceback

try:
    from docker.errors import DockerException
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from distutils.version import LooseVersion

from ansible.module_utils.docker.common import (
    AnsibleDockerClient,
    RequestException,
)

try:
    from ansible.module_utils.docker.common import docker_version, clean_dict_booleans_for_docker_api
except Exception as dummy:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass


def main():
    argument_spec = dict(
        containers=dict(type='bool', default=False),
        containers_filters=dict(type='dict'),
        images=dict(type='bool', default=False),
        images_filters=dict(type='dict'),
        networks=dict(type='bool', default=False),
        networks_filters=dict(type='dict'),
        volumes=dict(type='bool', default=False),
        volumes_filters=dict(type='dict'),
        builder_cache=dict(type='bool', default=False),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        # supports_check_mode=True,
        min_docker_api_version='1.25',
        min_docker_version='2.1.0',
    )

    # Version checks
    cache_min_version = '3.3.0'
    if client.module.params['builder_cache'] and client.docker_py_version < LooseVersion(cache_min_version):
        msg = "Error: Docker SDK for Python's version is %s. Minimum version required for builds option is %s. Use `pip install --upgrade docker` to upgrade."
        client.fail(msg % (docker_version, cache_min_version))

    try:
        result = dict()

        if client.module.params['containers']:
            filters = clean_dict_booleans_for_docker_api(client.module.params.get('containers_filters'))
            res = client.prune_containers(filters=filters)
            result['containers'] = res.get('ContainersDeleted') or []
            result['containers_space_reclaimed'] = res['SpaceReclaimed']

        if client.module.params['images']:
            filters = clean_dict_booleans_for_docker_api(client.module.params.get('images_filters'))
            res = client.prune_images(filters=filters)
            result['images'] = res.get('ImagesDeleted') or []
            result['images_space_reclaimed'] = res['SpaceReclaimed']

        if client.module.params['networks']:
            filters = clean_dict_booleans_for_docker_api(client.module.params.get('networks_filters'))
            res = client.prune_networks(filters=filters)
            result['networks'] = res.get('NetworksDeleted') or []

        if client.module.params['volumes']:
            filters = clean_dict_booleans_for_docker_api(client.module.params.get('volumes_filters'))
            res = client.prune_volumes(filters=filters)
            result['volumes'] = res.get('VolumesDeleted') or []
            result['volumes_space_reclaimed'] = res['SpaceReclaimed']

        if client.module.params['builder_cache']:
            res = client.prune_builds()
            result['builder_cache_space_reclaimed'] = res['SpaceReclaimed']

        client.module.exit_json(**result)
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
