# -*- coding: utf-8 -*-
# (c) 2018 Matt Martz <matt@sivel.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils import urls


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
