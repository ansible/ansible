# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.urls import fetch_file

import pytest
from units.compat.mock import MagicMock


def test_fetch_file(mocker):
    tempfile = mocker.patch('ansible.module_utils.urls.tempfile')
    tempfile.NamedTemporaryFile.side_effect = RuntimeError('boom')

    module = MagicMock()
    module.tmpdir = '/tmp'

    with pytest.raises(RuntimeError):
        fetch_file(module, 'http://ansible.com/foo.tar.gz?foo=%s' % ('bar' * 100))

    tempfile.NamedTemporaryFile.assert_called_once_with(dir='/tmp', prefix='foo.tar', suffix='.gz', delete=False)
