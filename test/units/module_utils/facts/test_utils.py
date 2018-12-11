# -*- coding: utf-8 -*-
#  Copyright: (c) 2017, Ansible Project
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division)
__metaclass__ = type

import os
import pytest
from ansible.module_utils.facts import utils

mount_data = [
    '/dev/null/not/a/real/mountpoint',
    '/proc'
]

file_data = [
    (
        "/dev/null/file/hello_world",
        ["Hello World"]
    ),
    (
        "/dev/null/no/content",
        []
    ),
]


@pytest.mark.parametrize("mount_point", mount_data, ids=['non_existent_mount', 'proc'])
def test_get_mount_size_with_different_values(mount_point):
    mount_info = utils.get_mount_size(mount_point)
    assert isinstance(mount_info, dict)


def test_oserror_on_statvfs(monkeypatch):
    def _os_statvfs(path):
        raise OSError('%s does not exist' % path)

    monkeypatch.setattr('os.statvfs', _os_statvfs)
    mount_info = utils.get_mount_size('/dev/null/doesnt/matter')
    assert isinstance(mount_info, dict)


@pytest.mark.parametrize("file_name, expected_file_content", file_data, ids=['hello_world_file', 'no_content_file'])
def test_get_file_lines(monkeypatch, file_name, expected_file_content):
    def _get_file_content(path, default=None, strip=True):
        if expected_file_content:
            return expected_file_content[0]
        return []

    monkeypatch.setattr('ansible.module_utils.facts.utils.get_file_content', _get_file_content)
    file_content = utils.get_file_lines(file_name)
    assert file_content == expected_file_content


@pytest.mark.parametrize("strip", [True, False], ids=['With_default_strip_true', 'With_strip_false'])
def test_get_file_content(strip):
    fake_file = os.path.join(os.path.dirname(__file__), './fixtures/test_file.txt')
    content = utils.get_file_content(fake_file, strip=strip)
    expected_content = 'Hello World\nThis file is used by test_utils'
    if strip is False:
        expected_content += "\n"
    assert content == expected_content


def test_get_file_content_without_file():
    fake_file = os.path.join(os.path.dirname(__file__), './fixtures/non_existent_file.txt')
    content = utils.get_file_content(fake_file)
    assert content is None
