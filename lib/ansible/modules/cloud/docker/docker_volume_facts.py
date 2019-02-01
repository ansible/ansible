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
module: docker_volume_facts
version_added: "2.8"
short_description: Retrieve facts about Docker volumes
description:
  - Performs largely the same function as the "docker volume inspect" CLI subcommand.
options:
  name:
    description:
      - Name of the volume to inspect.
    required: true
    type: str
    aliases:
      - volume_name

extends_documentation_fragment:
    - docker

author:
    - Felix Fontein (@felixfontein)

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
- name: Get infos on volume
  docker_volume_facts:
    name: mydata
  register: result

- name: Does volume exist?
  debug:
    msg: "The volume {{ 'exists' if result.exists else 'does not exist' }}"

- name: Print information about volume
  debug:
    var: result.docker_volume
  when: result.exists
'''

RETURN = '''
exists:
    description:
      - Returns whether the volume exists.
    type: bool
    returned: always
    sample: true
docker_volume:
    description:
      - Volume inspection results for the affected volume.
      - Will be C(None) if volume does not exist.
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

try:
    from docker.errors import NotFound
except ImportError:
    # missing docker-py handled in ansible.module_utils.docker_common
    pass

from ansible.module_utils.docker_common import AnsibleDockerClient


def get_existing_volume(client, volume_name):
    try:
        return client.inspect_volume(volume_name)
    except NotFound as dummy:
        return None
    except Exception as exc:
        client.module.fail_json(msg="Error inspecting volume: %s" % exc)


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

    volume = get_existing_volume(client, client.module.params['name'])

    client.module.exit_json(
        changed=False,
        exists=(True if volume else False),
        docker_volume=volume,
    )


if __name__ == '__main__':
    main()
