# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# Copyright: (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
import traceback
import json
import os
import re

from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.api import basic_auth_argument_spec

try:
    from urllib import quote_plus  # Python 2.X
except ImportError:
    from urllib.parse import quote_plus  # Python 3+

GITLAB_IMP_ERR = None
try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except ImportError:
    GITLAB_IMP_ERR = traceback.format_exc()
    HAS_GITLAB_PACKAGE = False
    gitlab = None


class GitlabApiConnection(object):
    def __init__(self, ansible_module):
        self.module = ansible_module

        if not HAS_GITLAB_PACKAGE:
            self.module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

        # handle deprecated module params; server_url, api_url, url are virtually
        # same thing. this can be removed with 2.10 release
        server_url = self.module.params.get('server_url')
        url = re.sub('/api.*', '', self.module.params.get('url', '') or '')
        api_url = re.sub('/api.*', '', self.module.params['api_url'])

        if api_url is not None:
            self.url = api_url
        elif url is not None:
            self.url = url
        elif server_url is not None:
            self.url = server_url

        api_user = self.module.params['api_username']
        login_user = self.module.params.get('login_user')  # deprecated in 2.10
        self.user = login_user if api_user is None else api_user

        api_password = self.module.params['api_password']
        login_password = self.module.params.get('login_password')  # deprecated in 2.10
        self.password = login_password if api_password is None else api_password

        api_token = self.module.params['api_token']
        login_token = self.module.params.get('login_token')  # deprecated in 2.10
        self.token = login_token if api_token is None else api_token

        self.validate_certs = self.module.params['validate_certs']
        self.config_files = map(os.path.expanduser, self.module.params['config_files'])

    def auth(self):
        try:
            # if none of the connection details were provided, try using
            # configuration file on the host
            if {self.user, self.password, self.token} == {None}:
                self.instance = gitlab.Gitlab.from_config(self.url, self.config_files)
            else:
                self.instance = gitlab.Gitlab(url=self.url, ssl_verify=self.validate_certs, email=self.user,
                                              password=self.password, private_token=self.token, api_version=4)
            self.instance.auth()
            return self.instance
        except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
            self.module.fail_json(msg="Failed to connect to Gitlab server: %s" % to_native(e))
        except (gitlab.exceptions.GitlabHttpError) as e:
            self.module.fail_json(msg="Failed to connect to Gitlab server: %s. \
                Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))


def request(module, api_url, project, path, access_token, private_token, rawdata='', method='GET'):
    url = "%s/v4/projects/%s%s" % (api_url, quote_plus(project), path)
    headers = {}
    if access_token:
        headers['Authorization'] = "Bearer %s" % access_token
    else:
        headers['Private-Token'] = private_token

    headers['Accept'] = "application/json"
    headers['Content-Type'] = "application/json"

    response, info = fetch_url(module=module, url=url, headers=headers, data=rawdata, method=method)
    status = info['status']
    content = ""
    if response:
        content = response.read()
    if status == 204:
        return True, content
    elif status == 200 or status == 201:
        return True, json.loads(content)
    else:
        return False, str(status) + ": " + content


def gitlab_auth_argument_spec():
    argument_spec = basic_auth_argument_spec()
    argument_spec.update(dict(
        server_url=dict(type='str', no_log=True, removed_in_version=2.10),
        login_user=dict(type='str', no_log=True, removed_in_version=2.10),
        login_password=dict(type='str', no_log=True, removed_in_version=2.10),
        api_token=dict(type='str', no_log=True, aliases=["login_token"]),
        config_files=dict(type='list', no_log=True, default=['/etc/python-gitlab.cfg', '~/.python-gitlab.cfg']),
    ))
    return argument_spec


gitlab_module_kwargs = dict(
    mutually_exclusive=[
        ['api_url', 'server_url', 'url'],
        ['api_username', 'login_user'],
        ['api_password', 'login_password'],
        ['api_username', 'api_token'],
        ['api_password', 'api_token'],
        ['login_user', 'login_token'],
        ['login_password', 'login_token']
    ],
    required_together=[
        ['api_username', 'api_password'],
        ['login_user', 'login_password'],
    ],
    required_one_of=[
        ['api_username', 'api_token', 'login_user', 'login_token', 'config_files']
    ],
    supports_check_mode=True,
)


def findProject(gitlab_instance, identifier):
    try:
        project = gitlab_instance.projects.get(identifier)
    except Exception as e:
        current_user = gitlab_instance.user
        try:
            project = gitlab_instance.projects.get(current_user.username + '/' + identifier)
        except Exception as e:
            return None

    return project


def findGroup(gitlab_instance, identifier):
    try:
        project = gitlab_instance.groups.get(identifier)
    except Exception as e:
        return None

    return project
