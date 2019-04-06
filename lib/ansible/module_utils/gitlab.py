# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# Copyright: (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
import json

from ansible.module_utils.urls import fetch_url
from ansible.module_utils.api import basic_auth_argument_spec

try:
    from urllib import quote_plus  # Python 2.X
except ImportError:
    from urllib.parse import quote_plus  # Python 3+


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
        ['api_url', 'server_url'],
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
