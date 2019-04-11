# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils import urls
from ansible.module_utils._text import to_native

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


def test_maybe_add_ssl_handler(mocker):
    mocker.patch.object(urls, 'HAS_SSL', new=False)
    with pytest.raises(urls.NoSSLError):
        urls.maybe_add_ssl_handler('https://ansible.com/', True)

    mocker.patch.object(urls, 'HAS_SSL', new=True)
    url = 'https://user:passwd@ansible.com/'
    handler = urls.maybe_add_ssl_handler(url, True)
    assert handler.hostname == 'ansible.com'
    assert handler.port == 443

    url = 'https://ansible.com:4433/'
    handler = urls.maybe_add_ssl_handler(url, True)
    assert handler.hostname == 'ansible.com'
    assert handler.port == 4433

    url = 'https://user:passwd@ansible.com:4433/'
    handler = urls.maybe_add_ssl_handler(url, True)
    assert handler.hostname == 'ansible.com'
    assert handler.port == 4433

    url = 'https://ansible.com/'
    handler = urls.maybe_add_ssl_handler(url, True)
    assert handler.hostname == 'ansible.com'
    assert handler.port == 443

    url = 'http://ansible.com/'
    handler = urls.maybe_add_ssl_handler(url, True)
    assert handler is None


def test_basic_auth_header():
    header = urls.basic_auth_header('user', 'passwd')
    assert header == b'Basic dXNlcjpwYXNzd2Q='


def test_ParseResultDottedDict():
    url = 'https://ansible.com/blog'
    parts = urls.urlparse(url)
    dotted_parts = urls.ParseResultDottedDict(parts._asdict())
    assert parts[0] == dotted_parts.scheme

    assert dotted_parts.as_list() == list(parts)


def test_unix_socket_patch_httpconnection_connect(mocker):
    unix_conn = mocker.patch.object(urls.UnixHTTPConnection, 'connect')
    conn = urls.httplib.HTTPConnection('ansible.com')
    with urls.unix_socket_patch_httpconnection_connect():
        conn.connect()
    assert unix_conn.call_count == 1
