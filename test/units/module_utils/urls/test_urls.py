# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils import urls
from ansible.module_utils._text import to_native
#import build_ssl_validation_error, HAS_SSLCONTEXT, HAS_URLLIB3_PYOPENSSLCONTEXT, HAS_URLLIB3_SSL_WRAP_SOCKET

import pytest


def test_build_ssl_validation_error(mocker):
    mocker.patch.object(urls, 'HAS_SSLCONTEXT', new=False)
    mocker.patch.object(urls, 'HAS_URLLIB3_PYOPENSSLCONTEXT', new=False)
    mocker.patch.object(urls, 'HAS_URLLIB3_SSL_WRAP_SOCKET', new=False)
    with pytest.raises(urls.SSLValidationError) as excinfo:
        urls.build_ssl_validation_error('hostname', 'port', 'paths', exc=None)

    assert 'python >= 2.7.9' in to_native(excinfo.value)
    assert 'the python executable used' in to_native(excinfo.value)
    assert 'urllib3' in to_native(excinfo.value)
    assert 'python >= 2.6' in to_native(excinfo.value)
    assert 'validate_certs=False' in to_native(excinfo.value)

    mocker.patch.object(urls, 'HAS_SSLCONTEXT', new=True)
    with pytest.raises(urls.SSLValidationError) as excinfo:
        urls.build_ssl_validation_error('hostname', 'port', 'paths', exc=None)

    assert 'validate_certs=False' in to_native(excinfo.value)

    mocker.patch.object(urls, 'HAS_SSLCONTEXT', new=False)
    mocker.patch.object(urls, 'HAS_URLLIB3_PYOPENSSLCONTEXT', new=True)
    mocker.patch.object(urls, 'HAS_URLLIB3_SSL_WRAP_SOCKET', new=True)

    mocker.patch.object(urls, 'HAS_SSLCONTEXT', new=True)
    with pytest.raises(urls.SSLValidationError) as excinfo:
        urls.build_ssl_validation_error('hostname', 'port', 'paths', exc=None)

    assert 'urllib3' not in to_native(excinfo.value)

    with pytest.raises(urls.SSLValidationError) as excinfo:
        urls.build_ssl_validation_error('hostname', 'port', 'paths', exc='BOOM')

    assert 'BOOM' in to_native(excinfo.value)
