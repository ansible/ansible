# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os

from ansible.module_utils.urls import open_url, urllib_request, HAS_SSLCONTEXT
from ansible.module_utils.urls import SSLValidationHandler, HTTPSClientAuthHandler, RedirectHandlerFactory


def test_open_url(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')

    r = open_url('https://ansible.com/')
    args = urlopen_mock.call_args[0]
    assert args[1] is None  # data, this is handled in the Request not urlopen
    assert args[2] == 10  # timeout

    req = args[0]
    assert req.headers == {}
    assert req.data is None
    assert req.get_method() == 'GET'

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    expected_handlers = (
        SSLValidationHandler,
        RedirectHandlerFactory(),  # factory, get handler
    )

    found_handlers = []
    for handler in handlers:
        if isinstance(handler, SSLValidationHandler) or handler.__class__.__name__ == 'RedirectHandler':
            found_handlers.append(handler)

    assert len(found_handlers) == 2


def test_open_url_http(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')

    r = open_url('http://ansible.com/')
    args = urlopen_mock.call_args[0]

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    found_handlers = []
    for handler in handlers:
        if isinstance(handler, SSLValidationHandler):
            found_handlers.append(handler)

    assert len(found_handlers) == 0


def test_open_url_ftp(mocker):
    mocker.patch('ansible.module_utils.urls.ParseResultDottedDict.as_list', side_effect=AssertionError)
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')

    # Using ftp scheme should prevent the AssertionError side effect to fire
    r = open_url('ftp://foo@ansible.com/')


def test_open_url_headers(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')
    r = open_url('http://ansible.com/', headers={'Foo': 'bar'})
    args = urlopen_mock.call_args[0]
    req = args[0]
    assert req.headers == {'Foo': 'bar'}


def test_open_url_username(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')
    r = open_url('http://ansible.com/', url_username='user')

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    expected_handlers = (
        urllib_request.HTTPBasicAuthHandler,
        urllib_request.HTTPDigestAuthHandler,
    )

    found_handlers = []
    for handler in handlers:
        if isinstance(handler, expected_handlers):
            found_handlers.append(handler)

    assert len(found_handlers) == 2


def test_open_url_username_force_basic(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')
    r = open_url('http://ansible.com/', url_username='user', url_password='passwd', force_basic_auth=True)

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    expected_handlers = (
        urllib_request.HTTPBasicAuthHandler,
        urllib_request.HTTPDigestAuthHandler,
    )

    found_handlers = []
    for handler in handlers:
        if isinstance(handler, expected_handlers):
            found_handlers.append(handler)

    assert len(found_handlers) == 0

    args = urlopen_mock.call_args[0]
    req = args[0]
    assert req.headers.get('Authorization') == b'Basic dXNlcjpwYXNzd2Q='


def test_open_url_auth_in_netloc(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')
    r = open_url('http://user:passwd@ansible.com/')
    args = urlopen_mock.call_args[0]
    req = args[0]
    assert req.get_full_url() == 'http://ansible.com/'

    opener = install_opener_mock.call_args[0][0]
    handlers = opener.handlers

    expected_handlers = (
        urllib_request.HTTPBasicAuthHandler,
        urllib_request.HTTPDigestAuthHandler,
    )

    found_handlers = []
    for handler in handlers:
        if isinstance(handler, expected_handlers):
            found_handlers.append(handler)

    assert len(found_handlers) == 2


def test_open_url_netrc(mocker, monkeypatch):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')

    here = os.path.dirname(__file__)

    monkeypatch.setenv('NETRC', os.path.join(here, 'fixtures/netrc'))
    r = open_url('http://ansible.com/')
    args = urlopen_mock.call_args[0]
    req = args[0]
    assert req.headers.get('Authorization') == b'Basic dXNlcjpwYXNzd2Q='

    r = open_url('http://foo.ansible.com/')
    args = urlopen_mock.call_args[0]
    req = args[0]
    assert 'Authorization' not in req.headers

    monkeypatch.setenv('NETRC', os.path.join(here, 'fixtures/netrc.nonexistant'))
    r = open_url('http://ansible.com/')
    args = urlopen_mock.call_args[0]
    req = args[0]
    assert 'Authorization' not in req.headers


def test_open_url_no_proxy(mocker):
    urlopen_mock = mocker.patch('ansible.module_utils.urls.urllib_request.urlopen')
    install_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.install_opener')
    build_opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request.build_opener')

    r = open_url('http://ansible.com/', use_proxy=False)

    handlers = build_opener_mock.call_args[0]
    found_handlers = []
    for handler in handlers:
        if isinstance(handler, urllib_request.ProxyHandler):
            found_handlers.append(handler)

    assert len(found_handlers) == 1
