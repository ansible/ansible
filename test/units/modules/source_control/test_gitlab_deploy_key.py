# -*- coding: utf-8 -*-
# Copyright (c) 2018 Marcus Watkins <marwatk@marcuswatkins.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests.mock import patch
from ansible.modules.source_control import gitlab_deploy_key
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic

import pytest
import json

fake_server_state = [
    {
        "id": 1,
        "title": "Public key",
        "key": 'ssh-rsa long/+base64//+string==',
        "created_at": "2013-10-02T10:12:29Z",
        "can_push": False
    },
]


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)


class FakeReader:
    def __init__(self, object):
        self.content = json.dumps(object, sort_keys=True)

    def read(self):
        return self.content


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


@pytest.fixture
def fetch_url_mock(mocker):
    return mocker.patch('ansible.module_utils.gitlab.fetch_url')


@pytest.fixture
def module_mock(mocker):
    return mocker.patch.multiple(basic.AnsibleModule,
                                 exit_json=exit_json,
                                 fail_json=fail_json)


def test_access_token_output(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'key': 'ssh-key foobar',
        'title': 'a title',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    first_call = fetch_url_mock.call_args_list[0][1]
    assert first_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/deploy_keys'
    assert first_call['headers']['Authorization'] == 'Bearer test-access-token'
    assert 'Private-Token' not in first_call['headers']
    assert first_call['method'] == 'GET'


def test_private_token_output(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'private_token': 'test-private-token',
        'project': 'foo/bar',
        'key': 'ssh-key foobar',
        'title': 'a title',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    first_call = fetch_url_mock.call_args_list[0][1]
    assert first_call['url'] == 'https://gitlab.example.com/api/v4/projects/foo%2Fbar/deploy_keys'
    assert first_call['headers']['Private-Token'] == 'test-private-token'
    assert 'Authorization' not in first_call['headers']
    assert first_call['method'] == 'GET'


def test_bad_http_first_response(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.side_effect = [[FakeReader("Permission denied"), {'status': 403}], [FakeReader("Permission denied"), {'status': 403}]]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'key': 'ssh-key foobar',
        'title': 'a title',
        'state': 'absent'
    })
    with pytest.raises(AnsibleFailJson):
        gitlab_deploy_key.main()


def test_bad_http_second_response(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.side_effect = [[FakeReader(fake_server_state), {'status': 200}], [FakeReader("Permission denied"), {'status': 403}]]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'key': 'ssh-key foobar',
        'title': 'a title',
        'state': 'present'
    })
    with pytest.raises(AnsibleFailJson):
        gitlab_deploy_key.main()


def test_delete_non_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'key': 'ssh-key foobar',
        'title': 'a title',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    assert result.value.args[0]['changed'] is False


def test_delete_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'key': 'ssh-rsa long/+base64//+string==',
        'title': 'a title',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/deploy_keys/1'
    assert second_call['method'] == 'DELETE'

    assert result.value.args[0]['changed'] is True


def test_add_new(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'key': 'ssh-key foobar',
        'title': 'a title',
        'state': 'present'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/deploy_keys'
    assert second_call['method'] == 'POST'
    assert second_call['data'] == '{"can_push": false, "key": "ssh-key foobar", "title": "a title"}'
    assert result.value.args[0]['changed'] is True


def test_update_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'title': 'Public key',
        'key': 'ssh-rsa long/+base64//+string==',
        'can_push': 'yes',
        'state': 'present'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/deploy_keys/1'
    assert second_call['method'] == 'PUT'
    assert second_call['data'] == ('{"can_push": true, "key": "ssh-rsa long/+base64//+string==", "title": "Public key"}')
    assert result.value.args[0]['changed'] is True


def test_unchanged_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'title': 'Public key',
        'key': 'ssh-rsa long/+base64//+string==',
        'can_push': 'no',
        'state': 'present'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_deploy_key.main()

    assert result.value.args[0]['changed'] is False
    assert fetch_url_mock.call_count == 1
