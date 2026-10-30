# -*- coding: utf-8 -*-
# (c) 2016, James Cammarata <jimi@sngx.net>
# (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import pytest

from ansible.module_utils import secrets
from ansible.module_utils._internal import _logging
from ansible.module_utils._internal._secrets import SecretMasker

ARGS = dict(foo=False, bar=[1, 2, 3], bam="bam", baz=u'baz')
ARGUMENT_SPEC = dict(
    foo=dict(default=True, type='bool'),
    bar=dict(default=[], type='list'),
    bam=dict(default="bam"),
    baz=dict(default=u"baz"),
    registered_secret=dict(default="My secret value"),
    password=dict(default=True),
    no_log=dict(default="you shouldn't see me", no_log=True),
)


HEADERS_ARGS = dict(
    headers=dict(Authorization='Bearer s3cr3t', Accept='application/json'),
    nested=dict(http_headers=dict(Cookie='session=abc')),
    unredirected_headers=['Authorization'],
)
HEADERS_ARGUMENT_SPEC = dict(
    headers=dict(type='dict'),
    nested=dict(type='dict', options=dict(http_headers=dict(type='dict'))),
    unredirected_headers=dict(type='list', elements='str'),
)


@pytest.mark.parametrize('am, stdin', [(ARGUMENT_SPEC, ARGS)], indirect=['am', 'stdin'])
def test_module_utils_basic__log_invocation(am, mocker, monkeypatch):

    temp_masker = SecretMasker()
    temp_masker.register_secret_text("Invoked")
    temp_masker.register_secret_text("My secret value")

    logger_mock = mocker.MagicMock()
    monkeypatch.setattr(_logging, 'log_to_system', logger_mock)
    monkeypatch.setattr(secrets, '_secret_masker', temp_masker)
    am._log_invocation()

    # Message is generated from a dict so it will be in an unknown order.
    # have to check this manually rather than with assert_called_with()
    args = logger_mock.call_args[0]
    assert len(args) == 1
    message = args[0]

    assert len(message) == \
        len('$REDACTED$ with bam=bam bar=[1, 2, 3] foo=False baz=baz no_log=$REDACTED$ password=$REDACTED$ registered_secret=$REDACTED$')

    assert message.startswith('$REDACTED$ with ')
    assert ' bam=bam' in message
    assert ' bar=[1, 2, 3]' in message
    assert ' foo=False' in message
    assert ' baz=baz' in message
    assert ' no_log=$REDACTED$' in message
    assert ' password=$REDACTED$' in message
    assert ' registered_secret=$REDACTED$' in message

    kwargs = logger_mock.call_args[1]
    assert kwargs == \
        dict(
            module_name='ansible_unittest',
            log_args={
                'foo': 'False',
                'bar': '[1, 2, 3]',
                'bam': 'bam',
                'baz': 'baz',
                'registered_secret': '$REDACTED$',
                'password': '$REDACTED$',
                'no_log': "$REDACTED$",
            },
            syslog_facility='LOG_USER',
            target_log_info=None,
        )


@pytest.mark.parametrize('am, stdin', [(HEADERS_ARGUMENT_SPEC, HEADERS_ARGS)], indirect=['am', 'stdin'])
def test_module_utils_basic__log_invocation_headers(am, mocker, monkeypatch):
    """Sensitive header values must be redacted from the logged message and from the journal fields."""
    logger_mock = mocker.MagicMock()
    monkeypatch.setattr(_logging, 'log_to_system', logger_mock)
    am._log_invocation()

    message = logger_mock.call_args[0][0]
    log_args = logger_mock.call_args[1]['log_args']

    assert 'Bearer s3cr3t' not in message
    assert 'session=abc' not in message

    # the names of the headers, and the values of the ones which carry no credentials, are still logged
    assert "headers={'Authorization': '$REDACTED$', 'Accept': 'application/json'}" in message
    assert "nested={'http_headers': {'Cookie': '$REDACTED$'}}" in message
    assert "unredirected_headers=['Authorization']" in message

    assert log_args['headers'] == "{'Authorization': '$REDACTED$', 'Accept': 'application/json'}"
    assert log_args['nested'] == "{'http_headers': {'Cookie': '$REDACTED$'}}"
    assert log_args['unredirected_headers'] == "['Authorization']"
