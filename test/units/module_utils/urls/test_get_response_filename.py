# -*- coding: utf-8 -*-
# (c) 2026 The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import email.message

import pytest

from ansible.module_utils.urls import get_response_filename


class FakeResponse:
    def __init__(self, url, content_disposition=None):
        self._url = url
        self._headers = email.message.Message()
        if content_disposition is not None:
            self._headers['content-disposition'] = content_disposition

    @property
    def headers(self):
        return self._headers

    def geturl(self):
        return self._url


@pytest.mark.parametrize(
    'url, content_disposition, wanted',
    (
        ('https://host/files/report.txt', None, 'report.txt'),
        ('https://host/files/report%20final.txt', None, 'report final.txt'),
        ('https://host/files/', None, 'files'),
        ('https://host/download', 'attachment; filename="report.txt"', 'report.txt'),
        ('https://host/download', 'attachment; filename="../../etc/passwd"', 'passwd'),
        # a server redirect to a path with percent-encoded separators must not
        # decode back into traversal after the basename has been taken
        ('https://host/x%2F..%2F..%2F..%2Fetc%2Fcron.d%2Fevil', None, 'evil'),
    )
)
def test_get_response_filename(url, content_disposition, wanted):
    assert get_response_filename(FakeResponse(url, content_disposition)) == wanted
