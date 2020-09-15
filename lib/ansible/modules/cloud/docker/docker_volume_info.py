#!/usr/bin/python
# coding: utf-8
#
# Copyright 2017 Red Hat | Ansible, Alex Grönholm <alex.gronholm@nextday.fi>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = u'''
module: docker_volume_info
version_added: "2.8"
short_description: Retrieve facts about Docker volumes
description:
  - Performs largely the same function as the "docker volume inspect" CLI subcommand.
options:
  name:
    description:
      - Name of the volume to inspect.
    type: str
    required: yes
    aliases:
      - volume_name

extends_documentation_fragment:
  - docker
  - docker.docker_py_1_documentation

author:
  - Felix Fontein (@felixfontein)

requirements:
  - "L(Docker SDK for Python,https://docker-py.readthedocs.io/en/stable/) >= 1.8.0 (use L(docker-py,https://pypi.org/project/docker-py/) for Python 2.6)"
  - "Docker API >= 1.21"
'''

EXAMPLES = '''
- name: Get infos on volume
  docker_volume_info:
    name: mydata
  register: result

- name: Does volume exist?
  debug:
    msg: "The volume {{ 'exists' if result.exists else 'does not exist' }}"

- name: Print information about volume
  debug:
    var: result.volume
  when: result.exists
'''

RETURN = '''
exists:
    description:
      - Returns whether the volume exists.
    type: bool
    returned: always
    sample: true
volume:
    description:
      - Volume inspection results for the affected volume.
      - Will be C(none) if volume does not exist.
    returned: success
    type: dict
    sample: '{
            "CreatedAt": "2018-12-09T17:43:44+01:00",
            "Driver": "local",
            "Labels": null,
            "Mountpoint": "/var/lib/docker/volumes/ansible-test-bd3f6172/_data",
            "Name": "ansible-test-bd3f6172",
            "Options": {},
            "Scope": "local"
        }'
'''

import traceback

try:
    from docker.errors import DockerException, NotFound
except ImportError:
    # missing Docker SDK for Python handled in ansible.module_utils.docker.common
    pass

from ansible.module_utils.docker.common import (
    AnsibleDockerClient,
    RequestException,
)


def get_existing_volume(client, volume_name):
    try:
        return client.inspect_volume(volume_name)
    except NotFound as dummy:
        return None
    except Exception as exc:
        client.fail("Error inspecting volume: %s" % exc)


def main():
    argument_spec = dict(
        name=dict(type='str', required=True, aliases=['volume_name']),
    )

    client = AnsibleDockerClient(
        argument_spec=argument_spec,
        supports_check_mode=True,
        min_docker_version='1.8.0',
        min_docker_api_version='1.21',
    )

    try:
        volume = get_existing_volume(client, client.module.params['name'])

        client.module.exit_json(
            changed=False,
            exists=(True if volume else False),
            volume=volume,
        )
    except DockerException as e:
        client.fail('An unexpected docker error occurred: {0}'.format(e), exception=traceback.format_exc())
    except RequestException as e:
        client.fail('An unexpected requests error occurred when docker-py tried to talk to the docker daemon: {0}'.format(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()
