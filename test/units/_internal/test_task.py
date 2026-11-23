# Copyright (c) 2026 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import copy

import pytest

from ansible._internal._task import UnifiedTaskResult, _redact_invocation_headers


def test_redact_invocation_headers():
    """The values of the well-known sensitive headers are redacted from the invocation at any depth."""
    result_data = dict(invocation=dict(module_args=dict(
        url='https://example.com',
        headers={'Authorization': 'Bearer s3cr3t', 'Accept': 'application/json'},
        nested=dict(http_headers={'Cookie': 'session=abc'}),
        items=[dict(headers={'Set-Cookie': 'session=abc'})],
        json_headers='{"Proxy-Authorization": "Basic Zm9v", "Accept": "application/json"}',
        unredirected_headers=['Authorization'],
        body=dict(Authorization='Bearer s3cr3t'),
    )))

    _redact_invocation_headers(result_data)

    assert result_data['invocation']['module_args'] == dict(
        url='https://example.com',
        headers={'Authorization': '$REDACTED$', 'Accept': 'application/json'},
        nested=dict(http_headers={'Cookie': '$REDACTED$'}),
        items=[dict(headers={'Set-Cookie': '$REDACTED$'})],
        json_headers='{"Proxy-Authorization": "$REDACTED$", "Accept": "application/json"}',
        # values which hold header names rather than header values are left as-is, as are non-header parameters
        unredirected_headers=['Authorization'],
        body=dict(Authorization='Bearer s3cr3t'),
    )


def test_redact_invocation_headers_configured(monkeypatch):
    """The headers configured with REDACT_HTTP_HEADERS are redacted in addition to the well-known ones."""
    monkeypatch.setenv('ANSIBLE_REDACT_HTTP_HEADERS', 'X-Api-Key, X-Token')

    result_data = dict(invocation=dict(module_args=dict(
        headers={'x-api-key': 's3cr3t', 'X-Token': 't0k', 'Authorization': 'Bearer s3cr3t', 'Accept': 'application/json'},
    )))

    _redact_invocation_headers(result_data)

    assert result_data['invocation']['module_args']['headers'] == {
        'x-api-key': '$REDACTED$',
        'X-Token': '$REDACTED$',
        'Authorization': '$REDACTED$',
        'Accept': 'application/json',
    }


@pytest.mark.parametrize('result_data', (
    {},
    dict(invocation=None),
    dict(invocation='CENSORED: no_log is set'),
    dict(invocation=dict(module_args=None)),
    dict(invocation=dict(module_args='src=/etc/motd dest=/var/tmp/m')),
))
def test_redact_invocation_headers_no_invocation(result_data):
    """A result without a usable invocation is left alone."""
    expected = copy.deepcopy(result_data)

    _redact_invocation_headers(result_data)

    assert result_data == expected


@pytest.mark.parametrize('factory', (
    UnifiedTaskResult.from_module_result_dict,
    UnifiedTaskResult.from_action_result_dict,
))
def test_redact_invocation_headers_from_result_dict(factory):
    """Results from both modules and action plugins are redacted as they are turned into a task result."""
    utr = factory(dict(changed=False, invocation=dict(module_args=dict(headers={'Authorization': 'Bearer s3cr3t'}))))

    assert utr.result_data['invocation']['module_args'] == dict(headers={'Authorization': '$REDACTED$'})
