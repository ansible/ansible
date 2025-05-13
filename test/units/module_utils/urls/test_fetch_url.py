# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import io
import socket
import sys
import http.client
import urllib.error
from http.cookiejar import Cookie

from ansible.module_utils.urls import fetch_url, ConnectionError

import pytest
from unittest.mock import MagicMock

BASE_URL = 'https://ansible.com/'


class AnsibleModuleExit(Exception):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ExitJson(AnsibleModuleExit):
    pass


class FailJson(AnsibleModuleExit):
    pass


@pytest.fixture
def open_url_mock(mocker):
    return mocker.patch('ansible.module_utils.urls.open_url')


@pytest.fixture
def fake_ansible_module():
    return FakeAnsibleModule()


class FakeAnsibleModule:
    def __init__(self):
        self.params = {}
        self.tmpdir = None

    def exit_json(self, *args, **kwargs):
        raise ExitJson(*args, **kwargs)

    def fail_json(self, *args, **kwargs):
        raise FailJson(*args, **kwargs)


def test_fetch_url(open_url_mock, fake_ansible_module):
    r, info = fetch_url(fake_ansible_module, BASE_URL)

    dummy, kwargs = open_url_mock.call_args

    open_url_mock.assert_called_once_with(BASE_URL, client_cert=None, client_key=None, cookies=kwargs['cookies'], data=None,
                                          follow_redirects='urllib2', force=False, force_basic_auth='', headers=None,
                                          http_agent='ansible-httpget', last_mod_time=None, method=None, timeout=10, url_password='', url_username='',
                                          use_proxy=True, validate_certs=True, use_gssapi=False, unix_socket=None, ca_path=None, unredirected_headers=None,
                                          decompress=True, ciphers=None, use_netrc=True)


def test_fetch_url_params(open_url_mock, fake_ansible_module):
    fake_ansible_module.params = {
        'validate_certs': False,
        'url_username': 'user',
        'url_password': 'passwd',
        'http_agent': 'ansible-test',
        'force_basic_auth': True,
        'follow_redirects': 'all',
        'client_cert': 'client.pem',
        'client_key': 'client.key',
    }

    r, info = fetch_url(fake_ansible_module, BASE_URL)

    dummy, kwargs = open_url_mock.call_args

    open_url_mock.assert_called_once_with(BASE_URL, client_cert='client.pem', client_key='client.key', cookies=kwargs['cookies'], data=None,
                                          follow_redirects='all', force=False, force_basic_auth=True, headers=None,
                                          http_agent='ansible-test', last_mod_time=None, method=None, timeout=10, url_password='passwd', url_username='user',
                                          use_proxy=True, validate_certs=False, use_gssapi=False, unix_socket=None, ca_path=None, unredirected_headers=None,
                                          decompress=True, ciphers=None, use_netrc=True)


def test_fetch_url_cookies(mocker, fake_ansible_module):
    def make_cookies(*args, **kwargs):
        cookies = kwargs['cookies']
        r = MagicMock()
        r.headers = http.client.HTTPMessage()
        add_header = r.headers.add_header
        r.info.return_value = r.headers
        for name, value in (('Foo', 'bar'), ('Baz', 'qux')):
            cookie = Cookie(
                version=0,
                name=name,
                value=value,
                port=None,
                port_specified=False,
                domain="ansible.com",
                domain_specified=True,
                domain_initial_dot=False,
                path="/",
                path_specified=True,
                secure=False,
                expires=None,
                discard=False,
                comment=None,
                comment_url=None,
                rest=None
            )
            cookies.set_cookie(cookie)
            add_header('Set-Cookie', '%s=%s' % (name, value))

        return r

    mocker = mocker.patch('ansible.module_utils.urls.open_url', new=make_cookies)

    r, info = fetch_url(fake_ansible_module, BASE_URL)

    assert info['cookies'] == {'Baz': 'qux', 'Foo': 'bar'}

    if sys.version_info < (3, 11):
        # Python sorts cookies in order of most specific (ie. longest) path first
        # items with the same path are reversed from response order
        assert info['cookies_string'] == 'Baz=qux; Foo=bar'
    else:
        # Python 3.11 and later preserve the Set-Cookie order.
        # See: https://github.com/python/cpython/pull/22745/
        assert info['cookies_string'] == 'Foo=bar; Baz=qux'

    # The key here has a `-` as opposed to what we see in the `uri` module that converts to `_`
    # Note: this is response order, which differs from cookies_string
    assert info['set-cookie'] == 'Foo=bar, Baz=qux'


def test_fetch_url_connectionerror(open_url_mock, fake_ansible_module):
    open_url_mock.side_effect = ConnectionError('TESTS')
    with pytest.raises(FailJson) as excinfo:
        fetch_url(fake_ansible_module, BASE_URL)

    assert excinfo.value.kwargs['msg'] == 'TESTS'
    assert BASE_URL == excinfo.value.kwargs['url']
    assert excinfo.value.kwargs['status'] == -1

    open_url_mock.side_effect = ValueError('TESTS')
    with pytest.raises(FailJson) as excinfo:
        fetch_url(fake_ansible_module, BASE_URL)

    assert excinfo.value.kwargs['msg'] == 'TESTS'
    assert BASE_URL == excinfo.value.kwargs['url']
    assert excinfo.value.kwargs['status'] == -1


def test_fetch_url_httperror(open_url_mock, fake_ansible_module):
    open_url_mock.side_effect = urllib.error.HTTPError(
        BASE_URL,
        500,
        'Internal Server Error',
        {'Content-Type': 'application/json'},
        io.StringIO('TESTS')
    )

    r, info = fetch_url(fake_ansible_module, BASE_URL)

    assert info == {'msg': 'HTTP Error 500: Internal Server Error', 'body': 'TESTS',
                    'status': 500, 'url': BASE_URL, 'content-type': 'application/json'}


def test_fetch_url_urlerror(open_url_mock, fake_ansible_module):
    open_url_mock.side_effect = urllib.error.URLError('TESTS')
    r, info = fetch_url(fake_ansible_module, BASE_URL)
    assert info == {'msg': 'Request failed: <urlopen error TESTS>', 'status': -1, 'url': BASE_URL}


def test_fetch_url_socketerror(open_url_mock, fake_ansible_module):
    open_url_mock.side_effect = socket.error('TESTS')
    r, info = fetch_url(fake_ansible_module, BASE_URL)
    assert info == {'msg': 'Connection failure: TESTS', 'status': -1, 'url': BASE_URL}


def test_fetch_url_exception(open_url_mock, fake_ansible_module):
    open_url_mock.side_effect = Exception('TESTS')
    r, info = fetch_url(fake_ansible_module, BASE_URL)
    exception = info.pop('exception')
    assert info == {'msg': 'An unknown error occurred: TESTS', 'status': -1, 'url': BASE_URL}
    assert "Exception: TESTS" in exception


def test_fetch_url_badstatusline(open_url_mock, fake_ansible_module):
    open_url_mock.side_effect = http.client.BadStatusLine('TESTS')
    r, info = fetch_url(fake_ansible_module, BASE_URL)
    assert info == {'msg': 'Connection failure: connection was closed before a valid response was received: TESTS', 'status': -1, 'url': BASE_URL}
