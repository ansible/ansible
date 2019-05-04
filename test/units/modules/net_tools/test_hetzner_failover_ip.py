# Copyright: (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import json
import pytest

from mock import MagicMock
from ansible.modules.net_tools import hetzner_failover_ip


class ModuleFailException(Exception):
    def __init__(self, msg, **kwargs):
        super(ModuleFailException, self).__init__(msg)
        self.fail_msg = msg
        self.fail_kwargs = kwargs


def get_module_mock():
    def f(msg, **kwargs):
        raise ModuleFailException(msg, **kwargs)

    module = MagicMock()
    module.fail_json = f
    module.from_json = json.loads
    return module


FETCH_URL_JSON_SUCCESS = [
    (
        (None, dict(
            body=json.dumps(dict(
                a='b'
            )).encode('utf-8'),
        )),
        None,
        (dict(
            a='b'
        ), None)
    ),
    (
        (None, dict(
            body=json.dumps(dict(
                error=dict(
                    code="foo",
                    status=400,
                    message="bar",
                ),
                a='b'
            )).encode('utf-8'),
        )),
        ['foo'],
        (dict(
            error=dict(
                code="foo",
                status=400,
                message="bar",
            ),
            a='b'
        ), 'foo')
    ),
]


FETCH_URL_JSON_FAIL = [
    (
        (None, dict(
            body=json.dumps(dict(
                error=dict(
                    code="foo",
                    status=400,
                    message="bar",
                ),
            )).encode('utf-8'),
        )),
        None,
        'Request failed: 400 foo (bar)'
    ),
    (
        (None, dict(
            body=json.dumps(dict(
                error=dict(
                    code="foo",
                    status=400,
                    message="bar",
                ),
            )).encode('utf-8'),
        )),
        ['bar'],
        'Request failed: 400 foo (bar)'
    ),
]


@pytest.mark.parametrize("return_value, accept_errors, result", FETCH_URL_JSON_SUCCESS)
def test_fetch_url_json(monkeypatch, return_value, accept_errors, result):
    module = get_module_mock()
    hetzner_failover_ip.fetch_url = MagicMock(return_value=return_value)

    assert hetzner_failover_ip.fetch_url_json(module, 'https://foo/bar', accept_errors=accept_errors) == result


@pytest.mark.parametrize("return_value, accept_errors, result", FETCH_URL_JSON_FAIL)
def test_fetch_url_json_fail(monkeypatch, return_value, accept_errors, result):
    module = get_module_mock()
    hetzner_failover_ip.fetch_url = MagicMock(return_value=return_value)

    with pytest.raises(ModuleFailException) as exc:
        hetzner_failover_ip.fetch_url_json(module, 'https://foo/bar', accept_errors=accept_errors)

    assert exc.value.fail_msg == result
    assert exc.value.fail_kwargs == dict()
