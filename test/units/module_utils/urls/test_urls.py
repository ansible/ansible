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


def test_get_ca_certs_skips_unreadable_directories(mocker):
    """A CA search path that exists but cannot be read should be skipped
    rather than aborting the whole scan.

    ``get_ca_certs`` builds a fixed search set that includes ``/etc/ansible``.
    If that path exists but is unreadable, ``os.listdir`` raised
    ``PermissionError`` instead of being skipped like the per-file ``OSError``
    handling already does, which broke ``ansible-galaxy`` installs on hosts
    where ``/etc/ansible`` is an inaccessible symlink
    (https://github.com/ansible/ansible/issues/87260).
    """
    # The real isdir/listdir may not touch /etc/ansible on every CI host, so
    # force the fallback path to look like an existing-but-unreadable directory.
    mocker.patch.object(
        urls.os.path,
        'isdir',
        side_effect=lambda p: True if str(p) == '/etc/ansible' else mocker.DEFAULT,
    )
    mocker.patch.object(
        urls.os,
        'listdir',
        side_effect=lambda p: (_ for _ in ()).throw(PermissionError(13, 'Permission denied', str(p))) if str(p) == '/etc/ansible' else mocker.DEFAULT,
    )

    # Must not raise: the PermissionError from listdir('/etc/ansible') is caught.
    data, paths_checked = urls.get_ca_certs()
    assert isinstance(data, (bytes, bytearray))
    assert '/etc/ansible' in paths_checked
