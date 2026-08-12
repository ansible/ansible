# -*- coding: utf-8 -*-
# (c) 2026 The Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.urls import mask_url


# for test data use 'secret' as part of any parameter that requires masking, avoid elsewhere
@pytest.mark.parametrize(
    'url, wanted',
    (
        ('http://nothingtoseehere.com', ('nothingtoseehere.com', 'http')),
        ('http://nothingtoseehere.com:80/stuff.asp?he=no', ('http://nothingtoseehere.com:80/stuff.asp?he=no',)),
        ('http://nothingtoseehere.com:80?password=intheclear&user=wrongbutweignore', ('wrongbut', 'intheclear', 'password')),
        ('https://secretuser@hideme.com/index.html', ('hideme.com', 'index.html', '*')),
        ('https://secretuser@hideme.com/index.html?token=nothidden&user=alsonothidden', ('token', 'nothidden', 'alsonothidden', 'user')),
        ('https://secretuser:secretpass@hideme.com/randomfile.html', ('randomfile.html')),
        ('https://secretuser:secretpass@hideme.com:443/protected.html', ('protected.html', '443')),
        ('ftp://secretuser:secretpass@files.insecure/subdir/intheclear.txt', ('subdir', 'intheclear.txt', 'ftp', 'files.insecure')),
        ('sftp://secretuser:secretpass@files.secure/subdir2/encrypted', ('encrypted', 'sftp')),
        ('ftps://secretuser:secretpass@file.secure/yolo.asc', ('yolo.asc', 'file.secure')),
        ('ftps://file.server/yolo.asc', ('yolo.asc')),
        ('ftps://secretuser:secretsecret@file.server/yolo.asc', ('file.server/yolo.asc')),
        ('redis://:secretpass@cache.internal:6379/0', ('cache.internal', '6379', 'redis')),
        ('amqp://:secretpw@rabbit.internal:5672/vhost', ('rabbit.internal', '5672', 'vhost')),
    )
)
def test_mask_url(url, wanted):

    masked = mask_url(url)
    assert 'secret' not in masked

    for notmasked in wanted:
        assert notmasked in masked


# `urlparse` raises ValueError for these, so `mask_url` must not propagate it to its callers.
@pytest.mark.parametrize(
    'url, wanted',
    (
        ('https://secretuser:secretpass@[::1/index.html', ('https://', '[::1/index.html', '****:****@')),
        ('https://secretuser@[::1/index.html', ('https://', '[::1/index.html', '****:****@')),
        ('ftp://secretuser:secretpass@[fe80::1:8080/pub/file.txt', ('ftp://', 'pub/file.txt', '****:****@')),
    )
)
def test_mask_url_unparsable(url, wanted):
    """An unparsable URL still has its userinfo masked, on a best-effort basis."""
    masked = mask_url(url)
    assert 'secret' not in masked

    for notmasked in wanted:
        assert notmasked in masked


@pytest.mark.parametrize(
    'url',
    (
        'https://[::1/index.html',
        'https://example.com]:443/index.html',
        'https://[v1.fe80::a+en1]:8080/index.html',
    )
)
def test_mask_url_unparsable_without_credentials(url):
    """An unparsable URL with no userinfo is returned intact so it remains useful for diagnostics."""
    assert mask_url(url) == url
