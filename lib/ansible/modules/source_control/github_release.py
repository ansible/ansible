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
    tag_name:
        required: false
        description:
            - Release tag name
            - Used when state=present|absent for release look up
	version_added: "2.4"
    state:
        required: false
        description:
            - Desired state of the release
            - Must not be used with `action`
        choices: [ 'absent', 'present' ]
	version_added: "2.4"
    target_commitish:
        required: false
        description:
            - Commit/branch ref
            - Required when state=present|absent
	version_added: "2.4"
    draft:
        required: false
        default: False
        description:
            - Specifies draft status for release (see GitHub release docs)
	version_added: "2.4"
    prerelease:
        required: false
        default: False
        description:
            - Specifies prerelease status for release (see GitHub release docs)
	version_added: "2.4"

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

- name: Ensure a release is present
  github_release:
    token: tokenabc1234567890
    user: testuser
    repo: testrepo
    state: present
    body: A release description
    tag_name: v0.1.2-beta+2234
    target_commitish: master
    name: Beta release 2234

- name: Ensure a release is not present
  github_release:
    token: tokenabc1234567890
    user: testuser
    repo: testrepo
    state: absent
    tag_name: v0.1.2-beta+2234
'''

RETURN = '''
action: latest_release
---
latest_release:
    description: Version of the latest release
    type: string
    returned: success
    sample: 1.1.0

state: present
---
release:
    description: Release details provided by GitHub
    type: dict
    returned: success
    sample: {}
'''

try:
    import github3

    HAS_GITHUB_API = True
except ImportError:
    HAS_GITHUB_API = False

import time
from ansible.module_utils.basic import AnsibleModule, get_exception

def find_release(module, repository):
    tag_name = module.params.get('tag_name')

    return repository.release_from_tag(tag_name)

def create_release(module, repository):
    params = module.params

    tag_name = params.get('tag_name')
    target_commitish = params.get('target_commitish')
    name = params.get('name')
    body = params.get('body')
    draft = params.get('draft')
    prerelease = params.get('prerelease')

    return repository.create_release(tag_name, target_commitish, name, body, draft, prerelease)

def update_release(module, release):
    params = module.params

    requires_update=False
    for attr_name in ['tag_name', 'target_commitish', 'name', 'body', 'draft', 'prerelease']:
        if getattr(release, attr_name) != params.get(attr_name):
            requires_update=True
            break

    if requires_update:
        tag_name = params.get('tag_name')
        target_commitish = params.get('target_commitish')
        name = params.get('name')
        body = params.get('body')
        draft = params.get('draft')
        prerelease = params.get('prerelease')

        return release.edit(tag_name, target_commitish, name, body, draft, prerelease)
    else:
        return None

def delete_release(_module, release):
    return release.delete()

def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(required=True),
            user=dict(required=True),
            password=dict(no_log=True),
            token=dict(no_log=True),
            action=dict(choices=['latest_release'], default=None),
            state=dict(choices=['absent', 'present'], default=None),
            body=dict(default=None),
            name=dict(default=None),
            tag_name=dict(required=False),
            target_commitish=dict(required=False),
            draft=dict(required=False, type='bool', default=False),
            prerelease=dict(type='bool', default=False)
        ),
        supports_check_mode=True,
        required_one_of=(('password', 'token'),),
        mutually_exclusive=(
            ('password', 'token'),
            ('state', 'action')
        ),
        required_if=(
            ('state', 'present', ('tag_name', 'target_commitish')),
            ('state', 'absent', ('tag_name', )),
        ),
    )

    if not HAS_GITHUB_API:
        module.fail_json(msg='Missing required github3 module (check docs or '
                             'install with: pip install github3.py==1.0.0a4)')

    repo = module.params['repo']
    user = module.params['user']
    password = module.params['password']
    login_token = module.params['token']
    action = module.params['action']
    state = module.params['state']

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

    else:
        release = find_release(module, repository)

        if state == 'absent':
            if isinstance(release, github3.null.NullObject):
                module.exit_json(changed=False, result="Release not found")
            else:
                if delete_release(module, release):
                    module.exit_json(changed=True, deleted=True)
                else:
                    module.fail_json(msg="Failed to delete release")

        elif state == 'present':
            if isinstance(release, github3.null.NullObject):
                release = create_release(module, repository)
                module.exit_json(changed=True, created=True, release=release.as_dict())

            else:
                update = update_release(module, release)
                if update is None:
                    module.exit_json(changed=False, release=release.as_dict())
                elif update:
                    time.sleep(1) # Remote change is quick, but not immediate
                    release = find_release(module, repository)
                    module.exit_json(changed=True, updated=True, release=release.as_dict())
                else:
                    module.fail_json(msg="Failed to update release")

        else:
            module.fail_json(msg="No action or state provided")

if __name__ == '__main__':
    main()
