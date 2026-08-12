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
        # a blank password still means userinfo is present, so it must be masked
        ('https://secretuser:@hideme.com/index.html', ('hideme.com', 'index.html', '****')),
        ('https://secretuser:@hideme.com:8443/index.html', ('hideme.com', '8443', '****')),
        ('ftp://secretuser:@files.insecure/pub/file.txt', ('files.insecure', 'pub/file.txt', '****')),
        # blank on both sides of the delimiter
        ('https://:@hideme.com/index.html', ('hideme.com', 'index.html', '****')),
        # a password containing '@' must not confuse host detection
        ('https://secretuser:secret@pass@hideme.com/index.html', ('hideme.com', 'index.html', '****')),
    )
)
def test_mask_url(url, wanted):

    masked = mask_url(url)
    assert 'secret' not in masked

    for notmasked in wanted:
        assert notmasked in masked


@pytest.mark.parametrize(
    'url',
    (
        'https://nocreds.example.com/index.html',
        'https://nocreds.example.com:8443/index.html?token=notuserinfo',
        'http://nocreds.example.com',
    )
)
def test_mask_url_without_userinfo_is_unchanged(url):
    """A URL carrying no userinfo is returned untouched."""
    assert mask_url(url) == url


@pytest.mark.parametrize(
    'url, expected',
    (
        ('https://secretuser@hideme.com/x', 'https://****@hideme.com/x'),
        ('https://secretuser:secretpass@hideme.com/x', 'https://****:****@hideme.com/x'),
        ('https://secretuser:@hideme.com/x', 'https://****:****@hideme.com/x'),
        ('https://:secretpass@hideme.com/x', 'https://****:****@hideme.com/x'),
        ('https://secretuser:secretpass@[::1]:8443/x', 'https://****:****@[::1]:8443/x'),
    )
)
def test_mask_url_exact_output(url, expected):
    """Everything except the userinfo survives masking intact."""
    assert mask_url(url) == expected
