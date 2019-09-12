#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
module: podman_image_info
author:
  - Sam Doran (@samdoran)
version_added: '2.8'
short_description: Gather info about images using podman
notes:
  - Podman may required elevated privileges in order to run properly.
description:
  - Gather info about images using C(podman)
options:
  executable:
    description:
      - Path to C(podman) executable if it is not in the C($PATH) on the machine running C(podman)
    default: 'podman'
    type: str
  name:
    description:
      - List of tags or UID to gather info about. If no name is given return info about all images.

"""

EXAMPLES = """
- name: Gather info for all images
  podman_image_info:

- name: Gather info on a specific image
  podman_image_info:
    name: nginx

- name: Gather info on several images
  podman_image_info:
    name:
      - redis
      - quay.io/bitnami/wildfly
"""

RETURN = """
images:
    description: info from all or specified images
    returned: always
    type: dict
    sample: [
        {
            "Annotations": {},
            "Architecture": "amd64",
            "Author": "",
            "Comment": "from Bitnami with love",
            "ContainerConfig": {
                "Cmd": [
                    "nami",
                    "start",
                    "--foreground",
                    "wildfly"
                ],
                "Entrypoint": [
                    "/app-entrypoint.sh"
                ],
                "Env": [
                    "PATH=/opt/bitnami/java/bin:/opt/bitnami/wildfly/bin:/opt/bitnami/nami/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                    "IMAGE_OS=debian-9",
                    "NAMI_VERSION=0.0.9-0",
                    "GPG_KEY_SERVERS_LIST=ha.pool.sks-keyservers.net \
hkp://p80.pool.sks-keyservers.net:80 keyserver.ubuntu.com hkp://keyserver.ubuntu.com:80 pgp.mit.edu",
                    "TINI_VERSION=v0.13.2",
                    "TINI_GPG_KEY=595E85A6B1B4779EA4DAAEC70B588DFF0527A9B7",
                    "GOSU_VERSION=1.10",
                    "GOSU_GPG_KEY=B42F6819007F00F88E364FD4036A9C25BF357DD4",
                    "BITNAMI_IMAGE_VERSION=14.0.1-debian-9-r12",
                    "BITNAMI_APP_NAME=wildfly",
                    "WILDFLY_JAVA_HOME=",
                    "WILDFLY_JAVA_OPTS=",
                    "WILDFLY_MANAGEMENT_HTTP_PORT_NUMBER=9990",
                    "WILDFLY_PASSWORD=bitnami",
                    "WILDFLY_PUBLIC_CONSOLE=true",
                    "WILDFLY_SERVER_AJP_PORT_NUMBER=8009",
                    "WILDFLY_SERVER_HTTP_PORT_NUMBER=8080",
                    "WILDFLY_SERVER_INTERFACE=0.0.0.0",
                    "WILDFLY_USERNAME=user",
                    "WILDFLY_WILDFLY_HOME=/home/wildfly",
                    "WILDFLY_WILDFLY_OPTS=-Dwildfly.as.deployment.ondemand=false"
                ],
                "ExposedPorts": {
                    "8080/tcp": {},
                    "9990/tcp": {}
                },
                "Labels": {
                    "maintainer": "Bitnami <containers@bitnami.com>"
                }
            },
            "Created": "2018-09-25T04:07:45.934395523Z",
            "Digest": "sha256:5c7d8e2dd66dcf4a152a4032a1d3c5a33458c67e1c1335edd8d18d738892356b",
            "GraphDriver": {
                "Data": {
                    "LowerDir": "/var/lib/containers/storage/overlay/a9dbf5616cc16919a8ac0dfc60aff87a72b5be52994c4649fcc91a089a12931\
f/diff:/var/lib/containers/storage/overlay/67129bd46022122a7d8b7acb490092af6c7ce244ce4fbd7d9e2d2b7f5979e090/diff:/var/lib/containers/storage/overlay/7c51242c\
4c5db5c74afda76d7fdbeab6965d8b21804bb3fc597dee09c770b0ca/diff:/var/lib/containers/storage/overlay/f97315dc58a9c002ba0cabccb9933d4b0d2113733d204188c88d72f75569b57b/diff:/var/lib/containers/storage/overlay/1dbde2dd497ddde2b467727125b900958a051a72561e58d29abe3d660dcaa9a7/diff:/var/lib/containers/storage/overlay/4aad9d80f30c3f0608f58173558b7554d84dee4dc4479672926eca29f75e6e33/diff:/var/lib/containers/storage/overlay/6751fc9b6868254870c062d75a511543fc8cfda2ce6262f4945f107449219632/diff:/var/lib/containers/storage/overlay/a27034d79081347421dd24d7e9e776c18271cd9a6e51053cb39af4d3d9c400e8/diff:/var/lib/containers/storage/overlay/537cf0045ed9cd7989f7944e7393019c81b16c1799a2198d8348cd182665397f/diff:/var/lib/containers/storage/overlay/27578615c5ae352af4e8449862d61aaf5c11b105a7d5905af55bd01b0c656d6e/diff:/var/lib/containers/storage/overlay/566542742840fe3034b3596f7cb9e62a6274c95a69f368f9e713746f8712c0b6/diff",
                    "MergedDir": "/var/lib/containers/storage/overlay/72bb96d6\
c53ad57a0b1e44cab226a6251598accbead40b23fac89c19ad8c25ca/merged",
                    "UpperDir": "/var/lib/containers/storage/overlay/72bb96d6c53ad57a0b1e44cab226a6251598accbead40b23fac89c19ad8c25ca/diff",
                    "WorkDir": "/var/lib/containers/storage/overlay/72bb96d6c53ad57a0b1e44cab226a6251598accbead40b23fac89c19ad8c25ca/work"
                },
                "Name": "overlay"
            },
            "Id": "bcacbdf7a119c0fa934661ca8af839e625ce6540d9ceb6827cdd389f823d49e0",
            "Labels": {
                "maintainer": "Bitnami <containers@bitnami.com>"
            },
            "ManifestType": "application/vnd.docker.distribution.manifest.v1+prettyjws",
            "Os": "linux",
            "Parent": "",
            "RepoDigests": [
                "quay.io/bitnami/wildfly@sha256:5c7d8e2dd66dcf4a152a4032a1d3c5a33458c67e1c1335edd8d18d738892356b"
            ],
            "RepoTags": [
                "quay.io/bitnami/wildfly:latest"
            ],
            "RootFS": {
                "Layers": [
                    "sha256:75391df2c87e076b0c2f72d20c95c57dc8be7ee684cc07273416cce622b43367",
                    "sha256:7dd303f041039bfe8f0833092673ac35f93137d10e0fbc4302021ea65ad57731",
                    "sha256:720d9edf0cd2a9bb56b88b80be9070dbfaad359514c70094c65066963fed485d",
                    "sha256:6a567ecbf97725501a634fcb486271999aa4591b633b4ae9932a46b40f5aaf47",
                    "sha256:59e9a6db8f178f3da868614564faabb2820cdfb69be32e63a4405d6f7772f68c",
                    "sha256:310a82ccb092cd650215ab375da8943d235a263af9a029b8ac26a281446c04db",
                    "sha256:36cb91cf4513543a8f0953fed785747ea18b675bc2677f3839889cfca0aac79e"
                ],
                "Type": "layers"
            },
            "Size": 569919342,
            "User": "",
            "Version": "17.06.0-ce",
            "VirtualSize": 569919342
        }
    ]
"""

import json

from ansible.module_utils.basic import AnsibleModule


def image_exists(module, executable, name):
    command = [executable, 'image', 'exists', name]
    rc, out, err = module.run_command(command)
    if rc == 1:
        return False
    elif 'Command "exists" not found' in err:
        # The 'exists' test is available in podman >= 0.12.1
        command = [executable, 'image', 'ls', '-q', name]
        rc2, out2, err2 = module.run_command(command)
        if rc2 != 0:
            return False
    return True


def filter_invalid_names(module, executable, name):
    valid_names = []
    names = name
    if not isinstance(name, list):
        names = [name]

    for name in names:
        if image_exists(module, executable, name):
            valid_names.append(name)

    return valid_names


def get_image_info(module, executable, name):
    names = name
    if not isinstance(name, list):
        names = [name]

    if len(names) > 0:
        command = [executable, 'image', 'inspect']
        command.extend(names)
        rc, out, err = module.run_command(command)

        if rc != 0:
            module.fail_json(msg="Unable to gather info for '{0}': {1}".format(', '.join(names), err))
        return out

    else:
        return json.dumps([])


def get_all_image_info(module, executable):
    command = [executable, 'image', 'ls', '-q']
    rc, out, err = module.run_command(command)
    name = out.strip().split('\n')
    out = get_image_info(module, executable, name)

    return out


def main():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(type='str', default='podman'),
            name=dict(type='list')
        ),
        supports_check_mode=True,
    )

    executable = module.params['executable']
    name = module.params.get('name')
    executable = module.get_bin_path(executable, required=True)

    if name:
        valid_names = filter_invalid_names(module, executable, name)
        results = json.loads(get_image_info(module, executable, valid_names))
    else:
        results = json.loads(get_all_image_info(module, executable))

    results = dict(
        changed=False,
        images=results
    )

    module.exit_json(**results)


if __name__ == '__main__':
    main()
