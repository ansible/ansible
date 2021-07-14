# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

from ansible.module_utils.urls import fetch_file

import pytest
from units.compat.mock import MagicMock


class FakeTemporaryFile:
    def __init__(self, name):
        self.name = name


def test_fetch_file(mocker):
    tempfile = mocker.patch('ansible.module_utils.urls.tempfile')
    tempfile.NamedTemporaryFile.side_effect = RuntimeError('boom')

    module = MagicMock()
    module.tmpdir = '/tmp'

    with pytest.raises(RuntimeError):
        fetch_file(module, 'http://ansible.com/foo.tar.gz?foo=%s' % ('bar' * 100))

    tempfile.NamedTemporaryFile.assert_called_once_with(dir='/tmp', prefix='foo.tar', suffix='.gz', delete=False)


@pytest.mark.parametrize(
    'url, prefix, suffix, expected', (
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