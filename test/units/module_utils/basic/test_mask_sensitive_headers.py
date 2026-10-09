# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils.basic import _mask_sensitive_headers


@pytest.mark.parametrize('name, value, expected', (
    # every sensitive header is masked, whatever its case, and the other headers are left alone
    ('headers',
     dict(Authorization='Bearer s3cr3t', Accept='application/json'),
     dict(Authorization='$REDACTED$', Accept='application/json')),
    ('headers',
     {'cookie': 'session=abc', 'Proxy-Authorization': 'Basic Zm9v', 'WWW-Authenticate': 'Basic realm=x',
      'Set-Cookie': 'session=abc', 'X-Request-Id': '1'},
     {'cookie': '$REDACTED$', 'Proxy-Authorization': '$REDACTED$', 'WWW-Authenticate': '$REDACTED$',
      'Set-Cookie': '$REDACTED$', 'X-Request-Id': '1'}),
    # a header mapping given as a JSON object is masked and re-serialized
    ('headers',
     '{"Authorization": "Bearer s3cr3t", "Accept": "application/json"}',
     '{"Authorization": "$REDACTED$", "Accept": "application/json"}'),
    # masking an already masked value changes nothing
    ('headers',
     '{"Authorization": "$REDACTED$"}',
     '{"Authorization": "$REDACTED$"}'),
    # parameters named after headers are masked whatever the prefix
    ('http_headers', dict(Cookie='session=abc'), dict(Cookie='$REDACTED$')),
    # a string which is not a JSON object cannot be masked reliably, so it is left as-is
    ('headers', 'Authorization: Bearer s3cr3t', 'Authorization: Bearer s3cr3t'),
    ('headers', "{'Authorization': 'Bearer s3cr3t'}", "{'Authorization': 'Bearer s3cr3t'}"),
    ('headers', '["Authorization"]', '["Authorization"]'),
    # values which hold header names rather than header values are left as-is
    ('unredirected_headers', ['Authorization'], ['Authorization']),
    ('headers', None, None),
    # parameters which are not headers are not masked, however they are named
    ('body', dict(Authorization='Bearer s3cr3t'), dict(Authorization='Bearer s3cr3t')),
    ('headers_to_send', dict(Authorization='Bearer s3cr3t'), dict(Authorization='Bearer s3cr3t')),
))
def test_mask_sensitive_headers(name, value, expected):
    assert _mask_sensitive_headers(name, value) == expected


def test_mask_sensitive_headers_does_not_mutate():
    """The argument must be left untouched, since it is the live module parameter."""
    headers = dict(Authorization='Bearer s3cr3t')

    assert _mask_sensitive_headers('headers', headers) == dict(Authorization='$REDACTED$')
    assert headers == dict(Authorization='Bearer s3cr3t')
