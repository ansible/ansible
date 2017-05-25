#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: github_release
short_description: Interact with GitHub Releases
description:
    - Fetch metadata about GitHub Releases
version_added: 2.2
options:
    token:
        description:
            - GitHub Personal Access Token for authenticating
        default: null
    user:
        required: true
        description:
            - The GitHub account that owns the repository
        default: null
    password:
        description:
            - The GitHub account password for the user
        default: null
        version_added: "2.4"
    repo:
        required: true
        description:
            - Repository name
        default: null
    action:
        required: true
        description:
            - Action to perform
        choices: [ 'latest_release' ]

author:
    - "Adrian Moisey (@adrianmoisey)"
requirements:
    - "github3.py >= 1.0.0a3"
'''

EXAMPLES = '''
- name: Get latest release of test/test
  github_release:
    token: tokenabc1234567890
    user: testuser
    repo: testrepo
    action: latest_release

- name: Get latest release of test repo using username and password. Ansible 2.4.
  github_release:
    user: testuser
    password: secret123
    repo: testrepo
    action: latest_release
'''

RETURN = '''
latest_release:
    description: Version of the latest release
    type: string
    returned: success
    sample: 1.1.0
'''

try:
    import github3

    HAS_GITHUB_API = True
except ImportError:
    HAS_GITHUB_API = False
from ansible.module_utils.basic import AnsibleModule, get_exception


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(required=True),
            user=dict(required=True),
            password=dict(no_log=True),
            token=dict(no_log=True),
            action=dict(required=True, choices=['latest_release']),
        ),
        supports_check_mode=True,
        required_one_of=(('password', 'token'),),
        mutually_exclusive=(('password', 'token'),),
    )

    if not HAS_GITHUB_API:
        module.fail_json(msg='Missing required github3 module (check docs or '
                             'install with: pip install github3.py==1.0.0a4)')

    repo = module.params['repo']
    user = module.params['user']
    password = module.params['password']
    login_token = module.params['token']
    action = module.params['action']

    # login to github
    try:
        if user and password:
            gh_obj = github3.login(user, password=password)
        elif login_token:
            gh_obj = github3.login(token=login_token)

        # test if we're actually logged in
        gh_obj.me()
    except github3.AuthenticationFailed:
        e = get_exception()
        module.fail_json(msg='Failed to connect to GitHub: %s' % e,
                         details="Please check username and password or token "
                                 "for repository %s" % repo)

    repository = gh_obj.repository(user, repo)

    if not repository:
        module.fail_json(msg="Repository %s/%s doesn't exist" % (user, repo))

    if action == 'latest_release':
        release = repository.latest_release()
        if release:
            module.exit_json(tag=release.tag_name)
        else:
            module.exit_json(tag=None)


if __name__ == '__main__':
    main()
