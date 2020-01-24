# (c) 2019 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import pytest

from ansible.module_utils.hetzner import BASE_URL
from ansible.modules.net_tools import hetzner_firewall


# ##########################################################
# ## General test framework

import json

from mock import MagicMock
from units.modules.utils import set_module_args
from ansible.module_utils.six.moves.urllib.parse import parse_qs


class FetchUrlCall:
    def __init__(self, method, status):
        assert method == method.upper(), \
            'HTTP method names are case-sensitive and should be upper-case (RFCs 7230 and 7231)'
        self.method = method
        self.status = status
        self.body = None
        self.headers = {}
        self.error_data = {}
        self.expected_url = None
        self.expected_headers = {}
        self.form_parse = False
        self.form_present = set()
        self.form_values = {}
        self.form_values_one = {}

    def result(self, body):
        self.body = body
        assert self.error_data.get('body') is None, 'Error body must not be given'
        return self

    def result_str(self, str_body):
        return self.result(str_body.encode('utf-8'))

    def result_json(self, json_body):
        return self.result(json.dumps(json_body).encode('utf-8'))

    def result_error(self, msg, body=None):
        self.error_data['msg'] = msg
        if body is not None:
            self.error_data['body'] = body
            assert self.body is None, 'Result must not be given if error body is provided'
        return self

    def expect_url(self, url):
        self.expected_url = url
        return self

    def return_header(self, name, value):
        assert value is not None
        self.headers[name] = value
        return self

    def expect_header(self, name, value):
        self.expected_headers[name] = value
        return self

    def expect_header_unset(self, name):
        self.expected_headers[name] = None
        return self

    def expect_form_present(self, key):
        self.form_parse = True
        self.form_present.append(key)
        return self

    def expect_form_value(self, key, value):
        self.form_parse = True
        self.form_values[key] = [value]
        return self

    def expect_form_value_absent(self, key):
        self.form_parse = True
        self.form_values[key] = []
        return self

    def expect_form_value_one_of(self, key, value):
        self.form_parse = True
        if key not in self.form_values_subset:
            self.form_values_subset[key] = set()
        self.form_values_subset[key].add(value)
        return self


class FetchUrlProxy:
    def __init__(self, calls):
        self.calls = calls
        self.index = 0

    def _validate_form(self, call, data):
        form = {}
        if data is not None:
            form = parse_qs(data, keep_blank_values=True)
        for k in call.form_present:
            assert k in form
        for k, v in call.form_values.items():
            if len(v) == 0:
                assert k not in form
            else:
                assert form[k] == v
        for k, v in call.form_values_one.items():
            assert v <= set(form[k])

    def _validate_headers(self, call, headers):
        given_headers = {}
        if headers is not None:
            for k, v in headers.items():
                given_headers[k.lower()] = v
        for k, v in call.expected_headers:
            if v is None:
                assert k.lower() not in given_headers, \
                    'Header "{0}" specified for fetch_url call, but should not be'.format(k)
            else:
                assert given_headers.get(k.lower()) == v, \
                    'Header "{0}" specified for fetch_url call, but with wrong value'.format(k)

    def __call__(self, module, url, data=None, headers=None, method=None,
                 use_proxy=True, force=False, last_mod_time=None, timeout=10,
                 use_gssapi=False, unix_socket=None, ca_path=None, cookies=None):
        assert self.index < len(self.calls), 'Got more fetch_url calls than expected'
        call = self.calls[self.index]
        self.index += 1

        # Validate call
        assert method == call.method
        if call.expected_url is not None:
            assert url == call.expected_url, \
                'Exepected URL does not match for fetch_url call'
        if call.expected_headers:
            self._validate_headers(call, headers)
        if call.form_parse:
            self._validate_form(call, data)

        # Compose result
        info = dict(status=call.status)
        for k, v in call.headers.items():
            info[k.lower()] = v
        info.update(call.error_data)
        res = object()
        if call.body is not None:
            res = MagicMock()
            res.read = MagicMock(return_value=call.body)
        return (res, info)

    def assert_is_done(self):
        assert self.index == len(self.calls), 'Got less fetch_url calls than expected'


class ModuleExitException(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs


class ModuleFailException(Exception):
    def __init__(self, kwargs):
        self.kwargs = kwargs


def run_module(mocker, module, arguments, fetch_url):
    def exit_json(module, **kwargs):
        module._return_formatted(kwargs)
        raise ModuleExitException(kwargs)

    def fail_json(module, **kwargs):
        module._return_formatted(kwargs)
        raise ModuleFailException(kwargs)

    mocker.patch('ansible.module_utils.hetzner.fetch_url', fetch_url)
    mocker.patch('ansible.module_utils.hetzner.time.sleep', lambda duration: None)
    mocker.patch('ansible.modules.net_tools.hetzner_firewall.AnsibleModule.exit_json', exit_json)
    mocker.patch('ansible.modules.net_tools.hetzner_firewall.AnsibleModule.fail_json', fail_json)
    set_module_args(arguments)
    module.main()


def run_module_success(mocker, module, arguments, fetch_url_calls):
    fetch_url = FetchUrlProxy(fetch_url_calls or [])
    with pytest.raises(ModuleExitException) as e:
        run_module(mocker, module, arguments, fetch_url)
    fetch_url.assert_is_done()
    return e.value.kwargs


def run_module_failed(mocker, module, arguments, fetch_url_calls):
    fetch_url = FetchUrlProxy(fetch_url_calls or [])
    with pytest.raises(ModuleFailException) as e:
        run_module(mocker, module, arguments, fetch_url)
    fetch_url.assert_is_done()
    return e.value.kwargs


# ##########################################################
# ## Hetzner firewall tests


# Tests for state (absent and present)


def test_absent_idempotency(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'absent',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'disabled'
    assert result['firewall']['status'] == 'disabled'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_absent_changed(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'absent',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('status', 'disabled'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'disabled'
    assert result['firewall']['status'] == 'disabled'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_present_idempotency(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_present_changed(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('status', 'active'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


# Tests for state (absent and present) with check mode


def test_absent_idempotency_check(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'absent',
        '_ansible_check_mode': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'disabled'
    assert result['firewall']['status'] == 'disabled'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_absent_changed_check(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'absent',
        '_ansible_check_mode': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'disabled'
    assert result['firewall']['status'] == 'disabled'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_present_idempotency_check(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        '_ansible_check_mode': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_present_changed_check(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        '_ansible_check_mode': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


# Tests for port


def test_port_idempotency(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'port': 'main',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['port'] == 'main'
    assert result['diff']['after']['port'] == 'main'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert result['firewall']['port'] == 'main'


def test_port_changed(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'port': 'main',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': True,
                'port': 'kvm',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('port', 'main'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['port'] == 'kvm'
    assert result['diff']['after']['port'] == 'main'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert result['firewall']['port'] == 'main'


# Tests for whitelist_hos


def test_whitelist_hos_idempotency(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'whitelist_hos': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['whitelist_hos'] is True
    assert result['diff']['after']['whitelist_hos'] is True
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert result['firewall']['whitelist_hos'] is True


def test_whitelist_hos_changed(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'whitelist_hos': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('whitelist_hos', 'true'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['whitelist_hos'] is False
    assert result['diff']['after']['whitelist_hos'] is True
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert result['firewall']['whitelist_hos'] is True


# Tests for wait_for_configured in getting status


def test_wait_get(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'wait_for_configured': True,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is False
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_wait_get_timeout(mocker):
    result = run_module_failed(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'wait_for_configured': True,
        'timeout': 0,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['msg'] == 'Timeout while waiting for firewall to be configured.'


def test_nowait_get(mocker):
    result = run_module_failed(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'wait_for_configured': False,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['msg'] == 'Firewall configuration cannot be read as it is not configured.'


# Tests for wait_for_configured in setting status


def test_wait_update(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'wait_for_configured': True,
        'state': 'present',
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'active'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


def test_wait_update_timeout(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'wait_for_configured': True,
        'timeout': 0,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'in process'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1
    assert 'Timeout while waiting for firewall to be configured.' in result['warnings']


def test_nowait_update(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'wait_for_configured': False,
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'disabled',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'in process',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'disabled'
    assert result['diff']['after']['status'] == 'active'
    assert result['firewall']['status'] == 'in process'
    assert result['firewall']['server_ip'] == '1.2.3.4'
    assert result['firewall']['server_number'] == 1


# Idempotency checks: different amount of input rules

def test_input_rule_len_change_0_1(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'rules': {
            'input': [
                {
                    'ip_version': 'ipv4',
                    'action': 'discard',
                },
            ],
        },
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [
                        {
                            'name': None,
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': None,
                            'src_ip': None,
                            'src_port': None,
                            'protocol': None,
                            'tcp_flags': None,
                            'action': 'discard',
                        },
                    ],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('status', 'active')
        .expect_form_value_absent('rules[input][0][name]')
        .expect_form_value('rules[input][0][ip_version]', 'ipv4')
        .expect_form_value_absent('rules[input][0][dst_ip]')
        .expect_form_value_absent('rules[input][0][dst_port]')
        .expect_form_value_absent('rules[input][0][src_ip]')
        .expect_form_value_absent('rules[input][0][src_port]')
        .expect_form_value_absent('rules[input][0][protocol]')
        .expect_form_value_absent('rules[input][0][tcp_flags]')
        .expect_form_value('rules[input][0][action]', 'discard')
        .expect_form_value_absent('rules[input][1][action]'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert len(result['diff']['before']['rules']['input']) == 0
    assert len(result['diff']['after']['rules']['input']) == 1
    assert result['firewall']['status'] == 'active'
    assert len(result['firewall']['rules']['input']) == 1


def test_input_rule_len_change_1_0(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'rules': {
        },
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [
                        {
                            'name': None,
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': None,
                            'src_ip': None,
                            'src_port': None,
                            'protocol': None,
                            'tcp_flags': None,
                            'action': 'discard',
                        },
                    ],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('status', 'active')
        .expect_form_value_absent('rules[input][0][action]'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert len(result['diff']['before']['rules']['input']) == 1
    assert len(result['diff']['after']['rules']['input']) == 0
    assert result['firewall']['status'] == 'active'
    assert len(result['firewall']['rules']['input']) == 0


def test_input_rule_len_change_1_2(mocker):
    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'rules': {
            'input': [
                {
                    'ip_version': 'ipv4',
                    'dst_port': 80,
                    'protocol': 'tcp',
                    'action': 'accept',
                },
                {
                    'ip_version': 'ipv4',
                    'action': 'discard',
                },
            ],
        },
    }, [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [
                        {
                            'name': None,
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': None,
                            'src_ip': None,
                            'src_port': None,
                            'protocol': None,
                            'tcp_flags': None,
                            'action': 'discard',
                        },
                    ],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
        FetchUrlCall('POST', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': False,
                'port': 'main',
                'rules': {
                    'input': [
                        {
                            'name': None,
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': '80',
                            'src_ip': None,
                            'src_port': None,
                            'protocol': 'tcp',
                            'tcp_flags': None,
                            'action': 'accept',
                        },
                        {
                            'name': None,
                            'ip_version': 'ipv4',
                            'dst_ip': None,
                            'dst_port': None,
                            'src_ip': None,
                            'src_port': None,
                            'protocol': None,
                            'tcp_flags': None,
                            'action': 'discard',
                        },
                    ],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
        .expect_form_value('status', 'active')
        .expect_form_value('rules[input][0][action]', 'accept')
        .expect_form_value('rules[input][1][action]', 'discard')
        .expect_form_value_absent('rules[input][2][action]'),
    ])
    assert result['changed'] is True
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert len(result['diff']['before']['rules']['input']) == 1
    assert len(result['diff']['after']['rules']['input']) == 2
    assert result['firewall']['status'] == 'active'
    assert len(result['firewall']['rules']['input']) == 2


# Idempotency checks: change one value


def create_params(parameter, *values):
    assert len(values) > 1
    result = []
    for i in range(1, len(values)):
        result.append((parameter, values[i - 1], values[i]))
    return result


def flatten(list_of_lists):
    result = []
    for l in list_of_lists:
        result.extend(l)
    return result


@pytest.mark.parametrize("parameter, before, after", flatten([
    create_params('name', None, '', 'Test', 'Test', 'foo', '', None),
    create_params('ip_version', 'ipv4', 'ipv4', 'ipv6', 'ipv6'),
    create_params('dst_ip', None, '1.2.3.4/24', '1.2.3.4/32', '1.2.3.4/32', None),
    create_params('dst_port', None, '80', '80-443', '80-443', None),
    create_params('src_ip', None, '1.2.3.4/24', '1.2.3.4/32', '1.2.3.4/32', None),
    create_params('src_port', None, '80', '80-443', '80-443', None),
    create_params('protocol', None, 'tcp', 'tcp', 'udp', 'udp', None),
    create_params('tcp_flags', None, 'syn', 'syn|fin', 'syn|fin', 'syn&fin', '', None),
    create_params('action', 'accept', 'accept', 'discard', 'discard'),
]))
def test_input_rule_value_change(mocker, parameter, before, after):
    input_call = {
        'ip_version': 'ipv4',
        'action': 'discard',
    }
    input_before = {
        'name': None,
        'ip_version': 'ipv4',
        'dst_ip': None,
        'dst_port': None,
        'src_ip': None,
        'src_port': None,
        'protocol': None,
        'tcp_flags': None,
        'action': 'discard',
    }
    input_after = {
        'name': None,
        'ip_version': 'ipv4',
        'dst_ip': None,
        'dst_port': None,
        'src_ip': None,
        'src_port': None,
        'protocol': None,
        'tcp_flags': None,
        'action': 'discard',
    }
    if after is not None:
        input_call[parameter] = after
    input_before[parameter] = before
    input_after[parameter] = after

    calls = [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [input_before],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ]

    changed = (before != after)
    if changed:
        after_call = (
            FetchUrlCall('POST', 200)
            .result_json({
                'firewall': {
                    'server_ip': '1.2.3.4',
                    'server_number': 1,
                    'status': 'active',
                    'whitelist_hos': False,
                    'port': 'main',
                    'rules': {
                        'input': [input_after],
                    },
                },
            })
            .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
            .expect_form_value('status', 'active')
            .expect_form_value_absent('rules[input][1][action]')
        )
        if parameter != 'ip_version':
            after_call.expect_form_value('rules[input][0][ip_version]', 'ipv4')
        if parameter != 'action':
            after_call.expect_form_value('rules[input][0][action]', 'discard')
        if after is not None:
            after_call.expect_form_value('rules[input][0][{0}]'.format(parameter), after)
        else:
            after_call.expect_form_value_absent('rules[input][0][{0}]'.format(parameter))
        calls.append(after_call)

    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'rules': {
            'input': [input_call],
        },
    }, calls)
    assert result['changed'] == changed
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert len(result['diff']['before']['rules']['input']) == 1
    assert len(result['diff']['after']['rules']['input']) == 1
    assert result['diff']['before']['rules']['input'][0][parameter] == before
    assert result['diff']['after']['rules']['input'][0][parameter] == after
    assert result['firewall']['status'] == 'active'
    assert len(result['firewall']['rules']['input']) == 1
    assert result['firewall']['rules']['input'][0][parameter] == after


# Idempotency checks: IP address normalization


@pytest.mark.parametrize("ip_version, parameter, before_normalized, after_normalized, after", [
    ('ipv4', 'src_ip', '1.2.3.4/32', '1.2.3.4/32', '1.2.3.4'),
    ('ipv6', 'src_ip', '1:2:3::4/128', '1:2:3::4/128', '1:2:3::4'),
    ('ipv6', 'dst_ip', '1:2:3::4/128', '1:2:3::4/128', '1:2:3:0::4'),
    ('ipv6', 'dst_ip', '::/0', '::/0', '0:0::0/0'),
])
def test_input_rule_ip_normalization(mocker, ip_version, parameter, before_normalized, after_normalized, after):
    assert ip_version in ('ipv4', 'ipv6')
    assert parameter in ('src_ip', 'dst_ip')
    input_call = {
        'ip_version': ip_version,
        'action': 'discard',
    }
    input_before = {
        'name': None,
        'ip_version': ip_version,
        'dst_ip': None,
        'dst_port': None,
        'src_ip': None,
        'src_port': None,
        'protocol': None,
        'tcp_flags': None,
        'action': 'discard',
    }
    input_after = {
        'name': None,
        'ip_version': ip_version,
        'dst_ip': None,
        'dst_port': None,
        'src_ip': None,
        'src_port': None,
        'protocol': None,
        'tcp_flags': None,
        'action': 'discard',
    }
    if after is not None:
        input_call[parameter] = after
    input_before[parameter] = before_normalized
    input_after[parameter] = after_normalized

    calls = [
        FetchUrlCall('GET', 200)
        .result_json({
            'firewall': {
                'server_ip': '1.2.3.4',
                'server_number': 1,
                'status': 'active',
                'whitelist_hos': True,
                'port': 'main',
                'rules': {
                    'input': [input_before],
                },
            },
        })
        .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL)),
    ]

    changed = (before_normalized != after_normalized)
    if changed:
        after_call = (
            FetchUrlCall('POST', 200)
            .result_json({
                'firewall': {
                    'server_ip': '1.2.3.4',
                    'server_number': 1,
                    'status': 'active',
                    'whitelist_hos': False,
                    'port': 'main',
                    'rules': {
                        'input': [input_after],
                    },
                },
            })
            .expect_url('{0}/firewall/1.2.3.4'.format(BASE_URL))
            .expect_form_value('status', 'active')
            .expect_form_value_absent('rules[input][1][action]')
        )
        after_call.expect_form_value('rules[input][0][ip_version]', ip_version)
        after_call.expect_form_value('rules[input][0][action]', 'discard')
        after_call.expect_form_value('rules[input][0][{0}]'.format(parameter), after_normalized)
        calls.append(after_call)

    result = run_module_success(mocker, hetzner_firewall, {
        'hetzner_user': '',
        'hetzner_password': '',
        'server_ip': '1.2.3.4',
        'state': 'present',
        'rules': {
            'input': [input_call],
        },
    }, calls)
    assert result['changed'] == changed
    assert result['diff']['before']['status'] == 'active'
    assert result['diff']['after']['status'] == 'active'
    assert len(result['diff']['before']['rules']['input']) == 1
    assert len(result['diff']['after']['rules']['input']) == 1
    assert result['diff']['before']['rules']['input'][0][parameter] == before_normalized
    assert result['diff']['after']['rules']['input'][0][parameter] == after_normalized
    assert result['firewall']['status'] == 'active'
    assert len(result['firewall']['rules']['input']) == 1
    assert result['firewall']['rules']['input'][0][parameter] == after_normalized
