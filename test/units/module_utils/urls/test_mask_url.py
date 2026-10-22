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


_ipv6 = 'Invalid IPv6 URL'


@pytest.mark.parametrize(
    'url, expected',
    (
        ('http://secretuser:secretpassword＠badunicodeat.com:80/file.html?nothing=something', None),
        ('http://secretuser:@badunicodeslash.com:443／file.html', None),
        ('http://secretuser@badunicodecolon.com：80', None),
        ('http://:secretpassword＠badunicodequestion.com:00/file.html？this=breaksparse', None),
        ('https://[::1/index.html', _ipv6),
        ('https://example.com]:443/index.html', _ipv6),
        ('https://[fe80::1:8080/index.html', _ipv6),
        ('//[::1/index.html', _ipv6),
        ('https://secretuser:secretpass@[::1/index.html', _ipv6),
        ('https://secretuser@[::1/index.html', _ipv6),
        ('ftp://secretuser:secretpass@[fe80::1:8080/pub/file.txt', _ipv6),
        ('https://:secretpass@::1]/index.html', _ipv6),
        ('https://secretuser:secretpass@[::1', _ipv6),
        # a scheme-relative url has no scheme to anchor on
        ('//secretuser:secretpass@[::1/index.html', _ipv6),
        # only `/` ends the authority, so a `?` or `#` cannot hide the userinfo
        ('https://[::1secretuser:sec?retpass@host/index.html', _ipv6),
        ('https://secretuser:secretpass@[::1#fragment', _ipv6),
        # the last `@` separates userinfo from host, matching how urlparse splits it
        ('https://secretuser:secret@pass@[::1/index.html', _ipv6),
        # combine!
        ('http://:secretpassword＠[::1/:01/badunicodeat/file.html？this=breaksparse', None),
    )
)
def test_mask_url_exceptions(url, expected):
    with pytest.raises(ValueError, match="^(?!.*secret).*$") as e:
        mask_url(url)

    msg = str(e)
    if expected is None:
        assert "ValueError('mask_url could not parse the url provided')" in msg
    else:
        assert 'mask_url could not parse the url provided' in msg
        assert expected in msg
