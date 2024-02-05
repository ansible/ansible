# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import os

from ansible.module_utils.urls import fetch_file

import pytest


class FakeTemporaryFile:
    def __init__(self, name):
        self.name = name


@pytest.mark.parametrize(
    'url, prefix, suffix, expected', (
        ('http://ansible.com/foo.tar.gz?foo=%s' % ('bar' * 100), 'foo', '.tar.gz', 'foo.tar.gz'),
        ('https://www.gnu.org/licenses/gpl-3.0.txt', 'gpl-3.0', '.txt', 'gpl-3.0.txt'),
        ('http://pyyaml.org/download/libyaml/yaml-0.2.5.tar.gz', 'yaml-0.2.5', '.tar.gz', 'yaml-0.2.5.tar.gz'),
        (
            'https://github.com/mozilla/geckodriver/releases/download/v0.26.0/geckodriver-v0.26.0-linux64.tar.gz',
            'geckodriver-v0.26.0-linux64',
            '.tar.gz',
            'geckodriver-v0.26.0-linux64.tar.gz'
        ),
    )
)
def test_file_multiple_extensions(mocker, url, prefix, suffix, expected):
    module = mocker.Mock()
    module.tmpdir = '/tmp'
    module.add_cleanup_file = mocker.Mock(side_effect=AttributeError('raised intentionally'))

    mock_NamedTemporaryFile = mocker.patch('ansible.module_utils.urls.tempfile.NamedTemporaryFile',
                                           return_value=FakeTemporaryFile(os.path.join(module.tmpdir, expected)))

    with pytest.raises(AttributeError, match='raised intentionally'):
        fetch_file(module, url)

    mock_NamedTemporaryFile.assert_called_with(dir=module.tmpdir, prefix=prefix, suffix=suffix, delete=False)
