# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.urls import HAS_SSLCONTEXT, RedirectHandlerFactory, urllib_request, urllib_error
from ansible.module_utils.six import StringIO

import pytest


@pytest.fixture
def urllib_req():
    req = urllib_request.Request(
        'https://ansible.com/'
    )
    return req


@pytest.fixture
def request_body():
    return StringIO('TESTS')


def test_no_redirs(urllib_req, request_body):
    handler = RedirectHandlerFactory('none', False)
    inst = handler()
    with pytest.raises(urllib_error.HTTPError):
        inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')


def test_urllib2_redir(urllib_req, request_body, mocker):
    redir_request_mock = mocker.patch('ansible.module_utils.urls.urllib_request.HTTPRedirectHandler.redirect_request')

    handler = RedirectHandlerFactory('urllib2', False)
    inst = handler()
    inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')

    redir_request_mock.assert_called_once_with(inst, urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')


def test_all_redir(urllib_req, request_body, mocker):
    req_mock = mocker.patch('ansible.module_utils.urls.RequestWithMethod')
    handler = RedirectHandlerFactory('all', False)
    inst = handler()
    inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')
    req_mock.assert_called_once_with('https://docs.ansible.com/', data=None, headers={}, method='GET', origin_req_host='ansible.com', unverifiable=True)


def test_all_redir_post(request_body, mocker):
    handler = RedirectHandlerFactory('all', False)
    inst = handler()

    req = urllib_request.Request(
        'https://ansible.com/',
        'POST'
    )

    req_mock = mocker.patch('ansible.module_utils.urls.RequestWithMethod')
    inst.redirect_request(req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')
    req_mock.assert_called_once_with('https://docs.ansible.com/', data=None, headers={}, method='GET', origin_req_host='ansible.com', unverifiable=True)


def test_redir_headers_removal(urllib_req, request_body, mocker):
    req_mock = mocker.patch('ansible.module_utils.urls.RequestWithMethod')
    handler = RedirectHandlerFactory('all', False)
    inst = handler()

    urllib_req.headers = {
        'Content-Type': 'application/json',
        'Content-Length': 100,
        'Foo': 'bar',
    }

    inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')
    req_mock.assert_called_once_with('https://docs.ansible.com/', data=None, headers={'Foo': 'bar'}, method='GET', origin_req_host='ansible.com',
                                     unverifiable=True)


def test_redir_url_spaces(urllib_req, request_body, mocker):
    req_mock = mocker.patch('ansible.module_utils.urls.RequestWithMethod')
    handler = RedirectHandlerFactory('all', False)
    inst = handler()

    inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/foo bar')

    req_mock.assert_called_once_with('https://docs.ansible.com/foo%20bar', data=None, headers={}, method='GET', origin_req_host='ansible.com',
                                     unverifiable=True)


def test_redir_safe(urllib_req, request_body, mocker):
    req_mock = mocker.patch('ansible.module_utils.urls.RequestWithMethod')
    handler = RedirectHandlerFactory('safe', False)
    inst = handler()
    inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')

    req_mock.assert_called_once_with('https://docs.ansible.com/', data=None, headers={}, method='GET', origin_req_host='ansible.com', unverifiable=True)


def test_redir_safe_not_safe(request_body):
    handler = RedirectHandlerFactory('safe', False)
    inst = handler()

    req = urllib_request.Request(
        'https://ansible.com/',
        'POST'
    )

    with pytest.raises(urllib_error.HTTPError):
        inst.redirect_request(req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')


def test_redir_no_error_on_invalid(urllib_req, request_body):
    handler = RedirectHandlerFactory('invalid', False)
    inst = handler()

    with pytest.raises(urllib_error.HTTPError):
        inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')


def test_redir_validate_certs(urllib_req, request_body, mocker):
    opener_mock = mocker.patch('ansible.module_utils.urls.urllib_request._opener')
    handler = RedirectHandlerFactory('all', True)
    inst = handler()
    inst.redirect_request(urllib_req, request_body, 301, '301 Moved Permanently', {}, 'https://docs.ansible.com/')

    assert opener_mock.add_handler.call_count == int(not HAS_SSLCONTEXT)


def test_redir_http_error_308_urllib2(urllib_req, request_body):
    handler = RedirectHandlerFactory('urllib2', False)
    inst = handler()

    with pytest.raises(urllib_error.HTTPError):
        inst.redirect_request(urllib_req, request_body, 308, '308 Permanent Redirect', {}, 'https://docs.ansible.com/')
