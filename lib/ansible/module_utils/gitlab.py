# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (lunik@tiwabbit.fr)
# Copyright: (c) 2018, Marcus Watkins <marwatk@marcuswatkins.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import
import json
from distutils.version import StrictVersion

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native

try:
    from urllib import quote_plus  # Python 2.X
except ImportError:
    from urllib.parse import quote_plus  # Python 3+

import traceback

GITLAB_IMP_ERR = None
try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    GITLAB_IMP_ERR = traceback.format_exc()
    HAS_GITLAB_PACKAGE = False


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


def gitlabAuthentication(module):
    gitlab_url = module.params['api_url']
    validate_certs = module.params['validate_certs']
    gitlab_user = module.params['api_username']
    gitlab_password = module.params['api_password']
    gitlab_token = module.params['api_token']

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg=missing_required_lib("python-gitlab"), exception=GITLAB_IMP_ERR)

    try:
        # python-gitlab library remove support for username/password authentication since 1.13.0
        # Changelog : https://github.com/python-gitlab/python-gitlab/releases/tag/v1.13.0
        # This condition allow to still support older version of the python-gitlab library
        if StrictVersion(gitlab.__version__) < StrictVersion("1.13.0"):
            gitlab_instance = gitlab.Gitlab(url=gitlab_url, ssl_verify=validate_certs, email=gitlab_user, password=gitlab_password,
                                            private_token=gitlab_token, api_version=4)
        else:
            gitlab_instance = gitlab.Gitlab(url=gitlab_url, ssl_verify=validate_certs, private_token=gitlab_token, api_version=4)

        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to GitLab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to GitLab server: %s. \
            GitLab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    return gitlab_instance
