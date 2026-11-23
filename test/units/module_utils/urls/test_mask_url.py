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
        pytest.param(
            "http://nothingtoseehere.com",
            ("nothingtoseehere.com", "http"),
            id="no-auth",
        ),
        pytest.param(
            "http://nothingtoseehere.com:80/stuff.asp?he=no",
            ("http://nothingtoseehere.com:80/stuff.asp?he=no",),
            id="with-port-and-query-string",
        ),
        pytest.param(
            "http://nothingtoseehere.com:80?password=intheclear&user=wrongbutweignore",
            ("wrongbut", "intheclear", "password"),
            id="with-port-and-query-string-and-userinfo",
        ),
        pytest.param(
            "https://secretuser@hideme.com/index.html",
            ("hideme.com", "index.html", "*"),
            id="with-userinfo-and-path",
        ),
        # token-as-username with an explicit, empty password (e.g. `token:@host`) must still be masked:
        pytest.param(
            "https://secretuser:@hideme.com/index.html",
            ("hideme.com", "index.html", "*"),
            id="token-as-username-with-empty-password",
        ),
        pytest.param(
            "https://secretuser@hideme.com/index.html?token=nothidden&user=alsonothidden",
            ("token", "nothidden", "alsonothidden", "user"),
            id="with-query-string-and-userinfo",
        ),
        pytest.param(
            "https://secretuser:secretpass@hideme.com/randomfile.html",
            ("randomfile.html"),
            id="with-userinfo-and-path-and-password",
        ),
        pytest.param(
            "https://secretuser:secretpass@hideme.com:443/protected.html",
            ("protected.html", "443"),
            id="with-port-and-userinfo-and-path-and-password",
        ),
        pytest.param(
            "ftp://secretuser:secretpass@files.insecure/subdir/intheclear.txt",
            ("subdir", "intheclear.txt", "ftp", "files.insecure"),
            id="ftp-uri",
        ),
        pytest.param(
            "sftp://secretuser:secretpass@files.secure/subdir2/encrypted",
            ("encrypted", "sftp"),
            id="sftp-uri",
        ),
        pytest.param(
            "ftps://secretuser:secretpass@file.secure/yolo.asc",
            ("yolo.asc", "file.secure"),
            id="ftps-uri",
        ),
        pytest.param(
            "ftps://file.server/yolo.asc",
            ("yolo.asc"),
            id="ftps-uri-with-path",
        ),
        pytest.param(
            "ftps://secretuser:secretsecret@file.server/yolo.asc",
            ("file.server/yolo.asc"),
            id="ftps-uri",
        ),
        pytest.param(
            "redis://:secretpass@cache.internal:6379/0",
            ("cache.internal", "6379", "redis"),
            id="redis-uri",
        ),
        pytest.param(
            "amqp://:secretpw@rabbit.internal:5672/vhost",
            ("rabbit.internal", "5672", "vhost"),
            id="amqp-uri",
        ),
    ),
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
        pytest.param(
            "http://secretuser:secretpassword＠badunicodeat.com:80/file.html?nothing=something",
            None,
            id="bad-unicode-at",
        ),
        pytest.param(
            "http://secretuser:@badunicodeslash.com:443／file.html",
            None,
            id="bad-unicode-slash",
        ),
        pytest.param(
            "http://secretuser@badunicodecolon.com：80", None, id="bad-unicode-colon"
        ),
        pytest.param(
            "http://:secretpassword＠badunicodequestion.com:00/file.html？this=breaksparse",
            None,
            id="bad-unicode-question",
        ),
        pytest.param(
            "https://[::1/index.html", _ipv6, id="incomplete-start-ipv6-bracket"
        ),
        pytest.param(
            "https://example.com]:443/index.html",
            _ipv6,
            id="incomplete-end-ipv6-bracket",
        ),
        pytest.param(
            "https://[fe80::1:8080/index.html",
            _ipv6,
            id="incomplete-start-ipv6-with-port",
        ),
        pytest.param(
            "//[::1/index.html",
            _ipv6,
            id="no-scheme-relative-ipv6",
        ),
        pytest.param(
            "https://secretuser:secretpass@[::1/index.html",
            _ipv6,
            id="ipv6-with-userinfo-and-path",
        ),
        pytest.param(
            "https://secretuser@[::1/index.html",
            _ipv6,
            id="ipv6-with-userinfo-no-password-and-path",
        ),
        pytest.param(
            "ftp://secretuser:secretpass@[fe80::1:8080/pub/file.txt",
            _ipv6,
            id="ftp-uri-with-incomplete-start-ipv6-with-port",
        ),
        pytest.param(
            "https://:secretpass@::1]/index.html",
            _ipv6,
            id="https-uri-with-incomplete-end-ipv6-with-port",
        ),
        pytest.param(
            "https://secretuser:secretpass@[::1",
            _ipv6,
            id="https-uri-with-ipv6-with-userinfo-and-host",
        ),
        # a scheme-relative url has no scheme to anchor on
        pytest.param(
            "//secretuser:secretpass@[::1/index.html",
            _ipv6,
            id="scheme-relative-ipv6",
        ),
        # only `/` ends the authority, so a `?` or `#` cannot hide the userinfo
        pytest.param(
            "https://[::1secretuser:sec?retpass@host/index.html",
            _ipv6,
            id="question-mark-in-path",
        ),
        pytest.param(
            "https://secretuser:secretpass@[::1#fragment",
            _ipv6,
            id="https-uri-with-fragment-in-path",
        ),
        # the last `@` separates userinfo from host, matching how urlparse splits it
        pytest.param(
            "https://secretuser:secret@pass@[::1/index.html",
            _ipv6,
            id="ampersand-in-path",
        ),
        # combine!
        pytest.param(
            "http://:secretpassword＠[::1/:01/badunicodeat/file.html？this=breaksparse",
            None,
            id="bad-unicode-at-and-question-mark-in-path",
        ),
    ),
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
