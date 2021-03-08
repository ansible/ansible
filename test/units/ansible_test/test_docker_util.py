# This file is part of Ansible
# -*- coding: utf-8 -*-
#
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

import pytest
from units.compat.mock import call, patch, MagicMock

# docker images quay.io/ansible/centos7-test-container --format '{{json .}}'
DOCKER_OUTPUT_MULTIPLE = """
{"Containers":"N/A","CreatedAt":"2020-06-11 17:05:58 -0500 CDT","CreatedSince":"3 months ago","Digest":"\u003cnone\u003e","ID":"b0f914b26cc1","Repository":"quay.io/ansible/centos7-test-container","SharedSize":"N/A","Size":"556MB","Tag":"1.17.0","UniqueSize":"N/A","VirtualSize":"555.6MB"}
{"Containers":"N/A","CreatedAt":"2020-06-11 17:05:58 -0500 CDT","CreatedSince":"3 months ago","Digest":"\u003cnone\u003e","ID":"b0f914b26cc1","Repository":"quay.io/ansible/centos7-test-container","SharedSize":"N/A","Size":"556MB","Tag":"latest","UniqueSize":"N/A","VirtualSize":"555.6MB"}
{"Containers":"N/A","CreatedAt":"2019-04-01 19:59:39 -0500 CDT","CreatedSince":"18 months ago","Digest":"\u003cnone\u003e","ID":"dd3d10e03dd3","Repository":"quay.io/ansible/centos7-test-container","SharedSize":"N/A","Size":"678MB","Tag":"1.8.0","UniqueSize":"N/A","VirtualSize":"678MB"}
""".lstrip()  # noqa: E501

PODMAN_OUTPUT = """
[
    {
        "id": "dd3d10e03dd3580de865560c3440c812a33fd7a1fca8ed8e4a1219ff3d809e3a",
        "names": [
            "quay.io/ansible/centos7-test-container:1.8.0"
        ],
        "digest": "sha256:6e5d9c99aa558779715a80715e5cf0c227a4b59d95e6803c148290c5d0d9d352",
        "created": "2019-04-02T00:59:39.234584184Z",
        "size": 702761933
    },
    {
        "id": "b0f914b26cc1088ab8705413c2f2cf247306ceeea51260d64c26894190d188bd",
        "names": [
            "quay.io/ansible/centos7-test-container:latest"
        ],
        "digest": "sha256:d8431aa74f60f4ff0f1bd36bc9a227bbb2066330acd8bf25e29d8614ee99e39c",
        "created": "2020-06-11T22:05:58.382459136Z",
        "size": 578513505
    }
]
""".lstrip()


@pytest.fixture
def docker_images():
    from ansible_test._internal.docker_util import docker_images
    return docker_images


@pytest.fixture
def ansible_test(ansible_test):
    import ansible_test
    return ansible_test


@pytest.fixture
def subprocess_error():
    from ansible_test._internal.util import SubprocessError
    return SubprocessError


@pytest.mark.parametrize(
    ('returned_items_count', 'patched_dc_stdout'),
    (
        (3, (DOCKER_OUTPUT_MULTIPLE, '')),
        (2, (PODMAN_OUTPUT, '')),
        (0, ('', '')),
    ),
    ids=('docker JSONL', 'podman JSON sequence', 'empty output'))
def test_docker_images(docker_images, mocker, returned_items_count, patched_dc_stdout):
    mocker.patch(
        'ansible_test._internal.docker_util.docker_command',
        return_value=patched_dc_stdout)
    ret = docker_images('', 'quay.io/ansible/centos7-test-container')
    assert len(ret) == returned_items_count


def test_podman_fallback(ansible_test, docker_images, subprocess_error, mocker):
    '''Test podman >2 && <2.2 fallback'''

    cmd = ['docker', 'images', 'quay.io/ansible/centos7-test-container', '--format', '{{json .}}']
    docker_command_results = [
        subprocess_error(cmd, status=1, stderr='function "json" not defined'),
        (PODMAN_OUTPUT, ''),
    ]
    mocker.patch(
        'ansible_test._internal.docker_util.docker_command',
        side_effect=docker_command_results)

    ret = docker_images('', 'quay.io/ansible/centos7-test-container')
    calls = [
        call(
            '',
            ['images', 'quay.io/ansible/centos7-test-container', '--format', '{{json .}}'],
            capture=True,
            always=True),
        call(
            '',
            ['images', 'quay.io/ansible/centos7-test-container', '--format', 'json'],
            capture=True,
            always=True),
    ]
    ansible_test._internal.docker_util.docker_command.assert_has_calls(calls)
    assert len(ret) == 2


def test_podman_no_such_image(ansible_test, docker_images, subprocess_error, mocker):
    '''Test podman "no such image" error'''

    cmd = ['docker', 'images', 'quay.io/ansible/centos7-test-container', '--format', '{{json .}}']
    exc = subprocess_error(cmd, status=1, stderr='no such image'),
    mocker.patch(
        'ansible_test._internal.docker_util.docker_command',
        side_effect=exc)
    ret = docker_images('', 'quay.io/ansible/centos7-test-container')
    assert ret == []
