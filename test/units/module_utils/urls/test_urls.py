# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from email.message import Message

from ansible.module_utils import urls


class _FakeResponse:
    def __init__(self, url, content_disposition=None):
        self._url = url
        self.headers = Message()
        if content_disposition is not None:
            self.headers['content-disposition'] = content_disposition

    def geturl(self):
        return self._url


def test_get_response_filename_from_content_disposition():
    resp = _FakeResponse('http://ansible.com/', 'attachment; filename="report.tar.gz"')
    assert urls.get_response_filename(resp) == 'report.tar.gz'


def test_get_response_filename_from_url_path():
    resp = _FakeResponse('http://ansible.com/files/data%20set.txt')
    assert urls.get_response_filename(resp) == 'data set.txt'


def test_get_response_filename_strips_encoded_traversal():
    resp = _FakeResponse('http://ansible.com/a/%2e%2e%2f%2e%2e%2fetc%2fpasswd')
    assert urls.get_response_filename(resp) == 'passwd'


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
    conn = urls.http.client.HTTPConnection('ansible.com')
    with urls.unix_socket_patch_httpconnection_connect():
        conn.connect()
    assert unix_conn.call_count == 1
