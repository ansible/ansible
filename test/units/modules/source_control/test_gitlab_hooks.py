# -*- coding: utf-8 -*-
# Copyright (c) 2018 Marcus Watkins <marwatk@marcuswatkins.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.compat.tests.mock import patch
from ansible.modules.source_control import gitlab_hooks
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic

import pytest
import json

from units.modules.utils import set_module_args


fake_server_state = [
    {
        "id": 1,
        "url": "https://notification-server.example.com/gitlab-hook",
        "project_id": 10,
        "push_events": True,
        "issues_events": True,
        "merge_requests_events": True,
        "tag_push_events": True,
        "note_events": True,
        "job_events": True,
        "pipeline_events": True,
        "wiki_page_events": True,
        "enable_ssl_verification": True,
        "created_at": "2012-10-12T17:04:47Z"
    },
]


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
        'hook_url': 'https://my-ci-server.example.com/gitlab-hook',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    first_call = fetch_url_mock.call_args_list[0][1]
    assert first_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/hooks'
    assert first_call['headers']['Authorization'] == 'Bearer test-access-token'
    assert 'Private-Token' not in first_call['headers']
    assert first_call['method'] == 'GET'


def test_private_token_output(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'private_token': 'test-private-token',
        'project': 'foo/bar',
        'hook_url': 'https://my-ci-server.example.com/gitlab-hook',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    first_call = fetch_url_mock.call_args_list[0][1]
    assert first_call['url'] == 'https://gitlab.example.com/api/v4/projects/foo%2Fbar/hooks'
    assert first_call['headers']['Private-Token'] == 'test-private-token'
    assert 'Authorization' not in first_call['headers']
    assert first_call['method'] == 'GET'


def test_bad_http_first_response(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.side_effect = [[FakeReader("Permission denied"), {'status': 403}], [FakeReader("Permission denied"), {'status': 403}]]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://my-ci-server.example.com/gitlab-hook',
        'state': 'absent'
    })
    with pytest.raises(AnsibleFailJson):
        gitlab_hooks.main()


def test_bad_http_second_response(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.side_effect = [[FakeReader(fake_server_state), {'status': 200}], [FakeReader("Permission denied"), {'status': 403}]]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://my-ci-server.example.com/gitlab-hook',
        'state': 'present'
    })
    with pytest.raises(AnsibleFailJson):
        gitlab_hooks.main()


def test_delete_non_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://my-ci-server.example.com/gitlab-hook',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    assert result.value.args[0]['changed'] is False


def test_delete_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://notification-server.example.com/gitlab-hook',
        'state': 'absent'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/hooks/1'
    assert second_call['method'] == 'DELETE'

    assert result.value.args[0]['changed'] is True


def test_add_new(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://my-ci-server.example.com/gitlab-hook',
        'state': 'present'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/hooks'
    assert second_call['method'] == 'POST'
    assert second_call['data'] == ('{"enable_ssl_verification": false, "issues_events": false, "job_events": false, '
                                   '"merge_requests_events": false, "note_events": false, "pipeline_events": false, "push_events": true, "tag_push_events": '
                                   'false, "token": null, "url": "https://my-ci-server.example.com/gitlab-hook", "wiki_page_events": false}')
    assert result.value.args[0]['changed'] is True


def test_update_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://notification-server.example.com/gitlab-hook',
        'push_events': 'yes',
        'issues_events': 'yes',
        'merge_requests_events': 'yes',
        'tag_push_events': 'yes',
        'note_events': 'yes',
        'job_events': 'yes',
        'pipeline_events': 'yes',
        'wiki_page_events': 'no',
        'enable_ssl_verification': 'yes',
        'state': 'present'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/hooks/1'
    assert second_call['method'] == 'PUT'
    assert second_call['data'] == ('{"enable_ssl_verification": true, "issues_events": true, "job_events": true, '
                                   '"merge_requests_events": true, "note_events": true, "pipeline_events": true, "push_events": true, "tag_push_events": '
                                   'true, "token": null, "url": "https://notification-server.example.com/gitlab-hook", "wiki_page_events": false}')
    assert result.value.args[0]['changed'] is True


def test_unchanged_existing(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://notification-server.example.com/gitlab-hook',
        'push_events': 'yes',
        'issues_events': 'yes',
        'merge_requests_events': 'yes',
        'tag_push_events': 'yes',
        'note_events': 'yes',
        'job_events': 'yes',
        'pipeline_events': 'yes',
        'wiki_page_events': 'yes',
        'enable_ssl_verification': 'yes',
        'state': 'present'
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    assert result.value.args[0]['changed'] is False
    assert fetch_url_mock.call_count == 1


def test_unchanged_existing_with_token(capfd, fetch_url_mock, module_mock):
    fetch_url_mock.return_value = [FakeReader(fake_server_state), {'status': 200}]
    set_module_args({
        'api_url': 'https://gitlab.example.com/api',
        'access_token': 'test-access-token',
        'project': '10',
        'hook_url': 'https://notification-server.example.com/gitlab-hook',
        'push_events': 'yes',
        'issues_events': 'yes',
        'merge_requests_events': 'yes',
        'tag_push_events': 'yes',
        'note_events': 'yes',
        'job_events': 'yes',
        'pipeline_events': 'yes',
        'wiki_page_events': 'yes',
        'enable_ssl_verification': 'yes',
        'state': 'present',
        'token': 'secret-token',
    })
    with pytest.raises(AnsibleExitJson) as result:
        gitlab_hooks.main()

    second_call = fetch_url_mock.call_args_list[1][1]

    assert second_call['url'] == 'https://gitlab.example.com/api/v4/projects/10/hooks/1'
    assert second_call['method'] == 'PUT'
    assert second_call['data'] == ('{"enable_ssl_verification": true, "issues_events": true, "job_events": true, '
                                   '"merge_requests_events": true, "note_events": true, "pipeline_events": true, "push_events": true, '
                                   '"tag_push_events": true, "token": "secret-token", "url": "https://notification-server.example.com/gitlab-hook", '
                                   '"wiki_page_events": true}')
    assert result.value.args[0]['changed'] is True
