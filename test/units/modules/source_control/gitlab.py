# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import

import sys

from httmock import response  # noqa
from httmock import urlmatch  # noqa

from units.compat import unittest

from gitlab import Gitlab


class FakeAnsibleModule(object):
    def __init__(self):
        self.check_mode = False

    def fail_json(self, **args):
        pass

    def exit_json(self, **args):
        pass


class GitlabModuleTestCase(unittest.TestCase):
    def setUp(self):
        unitest_python_version_check_requirement(self)

        self.mock_module = FakeAnsibleModule()

        self.gitlab_instance = Gitlab("http://localhost", private_token="private_token", api_version=4)


# Python 2.7+ is needed for python-gitlab
GITLAB_MINIMUM_PYTHON_VERSION = (2, 7)


# Verify if the current Python version is higher than GITLAB_MINIMUM_PYTHON_VERSION
def python_version_match_requirement():
    return sys.version_info >= GITLAB_MINIMUM_PYTHON_VERSION


# Skip unittest test case if python version don't match requirement
def unitest_python_version_check_requirement(unittest_testcase):
    if not python_version_match_requirement():
        unittest_testcase.skipTest("Python %s+ is needed for python-gitlab" % ",".join(map(str, GITLAB_MINIMUM_PYTHON_VERSION)))


'''
USER API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users", method="get")
def resp_find_user(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1, "username": "john_smith", "name": "John Smith", "state": "active",'
               '"avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",'
               '"web_url": "http://localhost:3000/john_smith"}, {"id": 2,'
               '"username": "jack_smith", "name": "Jack Smith", "state": "blocked",'
               '"avatar_url": "http://gravatar.com/../e32131cd8.jpeg",'
               '"web_url": "http://localhost:3000/jack_smith"}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users", method="post")
def resp_create_user(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "username": "john_smith", "name": "John Smith", "state": "active",'
               '"avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",'
               '"web_url": "http://localhost:3000/john_smith","created_at": "2012-05-23T08:00:58Z",'
               '"bio": null, "location": null, "public_email": "john@example.com", "skype": "",'
               '"linkedin": "", "twitter": "", "website_url": "", "organization": ""}')
    content = content.encode("utf-8")
    return response(201, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1", method="get")
def resp_get_user(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "username": "john_smith", "name": "John Smith",'
               '"state": "active",'
               '"avatar_url": "http://localhost:3000/uploads/user/avatar/1/cd8.jpeg",'
               '"web_url": "http://localhost:3000/john_smith",'
               '"created_at": "2012-05-23T08:00:58Z", "bio": null, "location": null,'
               '"public_email": "john@example.com", "skype": "", "linkedin": "",'
               '"twitter": "", "website_url": "", "organization": "", "is_admin": false}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1", method="get")
def resp_get_missing_user(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(404, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1", method="delete")
def resp_delete_user(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(204, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1", method="delete")
def resp_delete_missing_user(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(404, content, headers, None, 5, request)


'''
USER SSHKEY API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1/keys", method="get")
def resp_get_user_keys(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1, "title": "Public key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596'
               'k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfDzpvZK2H5E7eQa'
               'SeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",'
               '"created_at": "2014-08-01T14:47:39.080Z"},{"id": 3,'
               '"title": "Another Public key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596'
               'k6YjzGGphH2TUxwKzxcKDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfDzpvZK2H5E7eQaS'
               'eP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",'
               '"created_at": "2014-08-01T14:47:39.080Z"}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1/keys", method="post")
def resp_create_user_keys(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "title": "Private key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDA1YotVDm2mAyk2tPt4E7AHm01sS6JZmcUdRuSuA5z'
               'szUJzYPPUSRAX3BCgTqLqYx//UuVncK7YqLVSbbwjKR2Ez5lISgCnVfLVEXzwhv+xawxKWmI7hJ5S0tOv6MJ+Ixy'
               'Ta4xcKwJTwB86z22n9fVOQeJTR2dSOH1WJrf0PvRk+KVNY2jTiGHTi9AIjLnyD/jWRpOgtdfkLRc8EzAWrWlgNmH'
               '2WOKBw6za0az6XoG75obUdFVdW3qcD0xc809OHLi7FDf+E7U4wiZJCFuUizMeXyuK/SkaE1aee4Qp5R4dxTR4TP9'
               'M1XAYkf+kF0W9srZ+mhF069XD/zhUPJsvwEF",'
               '"created_at": "2014-08-01T14:47:39.080Z"}')
    content = content.encode("utf-8")
    return response(201, content, headers, None, 5, request)


'''
GROUP API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups", method="get")
def resp_find_group(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1, "name": "Foobar Group", "path": "foo-bar",'
               '"description": "An interesting group", "visibility": "public",'
               '"lfs_enabled": true, "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",'
               '"web_url": "http://localhost:3000/groups/foo-bar", "request_access_enabled": false,'
               '"full_name": "Foobar Group", "full_path": "foo-bar",'
               '"file_template_project_id": 1, "parent_id": null, "projects": []}, {"id": 2, "name": "BarFoo Group", "path": "bar-foor",'
               '"description": "An interesting group", "visibility": "public",'
               '"lfs_enabled": true, "avatar_url": "http://localhost:3000/uploads/group/avatar/2/bar.jpg",'
               '"web_url": "http://localhost:3000/groups/bar-foo", "request_access_enabled": false,'
               '"full_name": "BarFoo Group", "full_path": "bar-foo",'
               '"file_template_project_id": 1, "parent_id": null, "projects": []}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1", method="get")
def resp_get_group(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "name": "Foobar Group", "path": "foo-bar",'
               '"description": "An interesting group", "visibility": "public",'
               '"lfs_enabled": true, "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",'
               '"web_url": "http://localhost:3000/groups/foo-bar", "request_access_enabled": false,'
               '"full_name": "Foobar Group", "full_path": "foo-bar",'
               '"file_template_project_id": 1, "parent_id": null, "projects": [{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}]}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1", method="get")
def resp_get_missing_group(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(404, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups", method="post")
def resp_create_group(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "name": "Foobar Group", "path": "foo-bar",'
               '"description": "An interesting group", "visibility": "public",'
               '"lfs_enabled": true, "avatar_url": "http://localhost:3000/uploads/group/avatar/1/foo.jpg",'
               '"web_url": "http://localhost:3000/groups/foo-bar", "request_access_enabled": false,'
               '"full_name": "Foobar Group", "full_path": "foo-bar",'
               '"file_template_project_id": 1, "parent_id": null}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups", method="post")
def resp_create_subgroup(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 2, "name": "BarFoo Group", "path": "bar-foor",'
               '"description": "An interesting group", "visibility": "public",'
               '"lfs_enabled": true, "avatar_url": "http://localhost:3000/uploads/group/avatar/2/bar.jpg",'
               '"web_url": "http://localhost:3000/groups/foo-bar/bar-foo", "request_access_enabled": false,'
               '"full_name": "BarFoo Group", "full_path": "foo-bar/bar-foo",'
               '"file_template_project_id": 1, "parent_id": 1}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/users/1", method="delete")
def resp_delete_group(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(204, content, headers, None, 5, request)


'''
GROUP MEMBER API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1/members/1", method="get")
def resp_get_member(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "username": "raymond_smith", "name": "Raymond Smith", "state": "active",'
               '"avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",'
               '"web_url": "http://192.168.1.8:3000/root", "expires_at": "2012-10-22T14:13:35Z", "access_level": 30}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1/members", method="get")
def resp_find_member(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1, "username": "raymond_smith", "name": "Raymond Smith", "state": "active",'
               '"avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",'
               '"web_url": "http://192.168.1.8:3000/root", "expires_at": "2012-10-22T14:13:35Z", "access_level": 30},{'
               '"id": 2, "username": "john_doe", "name": "John Doe","state": "active",'
               '"avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",'
               '"web_url": "http://192.168.1.8:3000/root","expires_at": "2012-10-22T14:13:35Z",'
               '"access_level": 30}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1/members", method="post")
def resp_add_member(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "username": "raymond_smith", "name": "Raymond Smith",'
               '"state": "active",'
               '"avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",'
               '"web_url": "http://192.168.1.8:3000/root", "expires_at": "2012-10-22T14:13:35Z",'
               '"access_level": 30}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1/members/1", method="put")
def resp_update_member(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1, "username": "raymond_smith", "name": "Raymond Smith",'
               '"state": "active",'
               '"avatar_url": "https://www.gravatar.com/avatar/c2525a7f58ae3776070e44c106c48e15?s=80&d=identicon",'
               '"web_url": "http://192.168.1.8:3000/root", "expires_at": "2012-10-22T14:13:35Z",'
               '"access_level": 10}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


'''
DEPLOY KEY API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/deploy_keys", method="get")
def resp_find_project_deploy_key(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1,"title": "Public key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxc'
               'KDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",'
               '"created_at": "2013-10-02T10:12:29Z"},{"id": 3,"title": "Another Public key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxc'
               'KDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",'
               '"created_at": "2013-10-02T11:12:29Z"}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/deploy_keys/1", method="get")
def resp_get_project_deploy_key(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"title": "Public key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxc'
               'KDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",'
               '"created_at": "2013-10-02T10:12:29Z"}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/deploy_keys", method="post")
def resp_create_project_deploy_key(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"title": "Public key",'
               '"key": "ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAIEAiPWx6WM4lhHNedGfBpPJNPpZ7yKu+dnn1SJejgt4596k6YjzGGphH2TUxwKzxc'
               'KDKKezwkpfnxPkSMkuEspGRt/aZZ9wa++Oi7Qkr8prgHc4soW6NUlfDzpvZK2H5E7eQaSeP3SAwGmQKUFHCddNaP0L+hM7zhFNzjFvpaMgJw0=",'
               '"created_at": "2013-10-02T10:12:29Z"}')
    content = content.encode("utf-8")
    return response(201, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/deploy_keys/1", method="delete")
def resp_delete_project_deploy_key(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(204, content, headers, None, 5, request)


'''
PROJECT API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects", method="get")
def resp_find_project(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1", method="get")
def resp_get_project(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/foo-bar%2Fdiaspora-client", method="get")
def resp_get_project_by_name(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1/projects", method="get")
def resp_find_group_project(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/groups/1/projects/1", method="get")
def resp_get_group_project(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects", method="post")
def resp_create_project(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"description": null, "default_branch": "master",'
               '"ssh_url_to_repo": "git@example.com:diaspora/diaspora-client.git",'
               '"http_url_to_repo": "http://example.com/diaspora/diaspora-client.git",'
               '"web_url": "http://example.com/diaspora/diaspora-client",'
               '"readme_url": "http://example.com/diaspora/diaspora-client/blob/master/README.md",'
               '"tag_list": ["example","disapora client"],"name": "Diaspora Client",'
               '"name_with_namespace": "Diaspora / Diaspora Client","path": "diaspora-client",'
               '"path_with_namespace": "diaspora/diaspora-client","created_at": "2013-09-30T13:46:02Z",'
               '"last_activity_at": "2013-09-30T13:46:02Z","forks_count": 0,'
               '"avatar_url": "http://example.com/uploads/project/avatar/4/uploads/avatar.png",'
               '"star_count": 0}')
    content = content.encode("utf-8")
    return response(201, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1", method="delete")
def resp_delete_project(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")

    return response(204, content, headers, None, 5, request)


'''
HOOK API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/hooks", method="get")
def resp_find_project_hook(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"id": 1,"url": "http://example.com/hook","project_id": 3,'
               '"push_events": true,"push_events_branch_filter": "","issues_events": true,'
               '"confidential_issues_events": true,"merge_requests_events": true,'
               '"tag_push_events": true,"note_events": true,"job_events": true,'
               '"pipeline_events": true,"wiki_page_events": true,"enable_ssl_verification": true,'
               '"created_at": "2012-10-12T17:04:47Z"}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/hooks/1", method="get")
def resp_get_project_hook(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"url": "http://example.com/hook","project_id": 3,'
               '"push_events": true,"push_events_branch_filter": "","issues_events": true,'
               '"confidential_issues_events": true,"merge_requests_events": true,'
               '"tag_push_events": true,"note_events": true,"job_events": true,'
               '"pipeline_events": true,"wiki_page_events": true,"enable_ssl_verification": true,'
               '"created_at": "2012-10-12T17:04:47Z"}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/hooks", method="post")
def resp_create_project_hook(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"id": 1,"url": "http://example.com/hook","project_id": 3,'
               '"push_events": true,"push_events_branch_filter": "","issues_events": true,'
               '"confidential_issues_events": true,"merge_requests_events": true,'
               '"tag_push_events": true,"note_events": true,"job_events": true,'
               '"pipeline_events": true,"wiki_page_events": true,"enable_ssl_verification": true,'
               '"created_at": "2012-10-12T17:04:47Z"}')
    content = content.encode("utf-8")
    return response(201, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/projects/1/hooks/1", method="delete")
def resp_delete_project_hook(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(204, content, headers, None, 5, request)


'''
HOOK API
'''


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/runners/all", method="get")
def resp_find_runners(url, request):
    headers = {'content-type': 'application/json'}
    content = ('[{"active": true,"description": "test-1-20150125","id": 1,'
               '"is_shared": false,"ip_address": "127.0.0.1","name": null,'
               '"online": true,"status": "online"},{"active": true,'
               '"description": "test-2-20150125","id": 2,"ip_address": "127.0.0.1",'
               '"is_shared": false,"name": null,"online": false,"status": "offline"}]')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/runners/1", method="get")
def resp_get_runner(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"active": true,"description": "test-1-20150125","id": 1,'
               '"is_shared": false,"ip_address": "127.0.0.1","name": null,'
               '"online": true,"status": "online"}')
    content = content.encode("utf-8")
    return response(200, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/runners", method="post")
def resp_create_runner(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{"active": true,"description": "test-1-20150125","id": 1,'
               '"is_shared": false,"ip_address": "127.0.0.1","name": null,'
               '"online": true,"status": "online"}')
    content = content.encode("utf-8")
    return response(201, content, headers, None, 5, request)


@urlmatch(scheme="http", netloc="localhost", path="/api/v4/runners/1", method="delete")
def resp_delete_runner(url, request):
    headers = {'content-type': 'application/json'}
    content = ('{}')
    content = content.encode("utf-8")
    return response(204, content, headers, None, 5, request)
