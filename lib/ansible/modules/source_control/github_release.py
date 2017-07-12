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


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: github_release
short_description: Interact with GitHub Releases
description:
    - Manage GitHub releases
    - Fetch metadata about Github Releases
version_added: 2.2
options:
    token:
        required: true
        description:
            - Github Personal Access Token for authenticating
    user:
        required: true
        description:
            - The GitHub account that owns the repository
    repo:
        required: true
        description:
            - Repository name
    name:
        required: false
        description:
            - Release name
            - Used when state=present for creation or update
    tag_name:
        required: false
        description:
            - Release tag name
            - Used when state=present|absent for release look up
    state:
        required: false
        description:
            - Desired state of the release
            - Must not be used with `action`
        choices: [ 'absent', 'present' ]
    action:
        required: false
        description:
            - Action to perform
        choices: [ 'latest_release' ]
    target_commitish:
        required: false
        description:
            - Commit/branch ref
            - Required when state=present|absent
    draft:
        required: false
        default: False
        description:
            - Specifies draft status for release (see GitHub release docs)
    prerelease:
        required: false
        default: False
        description:
            - Specifies prerelease status for release (see GitHub release docs)

author:
    - "Adrian Moisey (@adrianmoisey)"
    - "James Kassemi (@jkassemi)"
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

def update_release(module, repository):
    params = module.params

    tag_name = params.get('tag_name')
    target_commitish = params.get('target_commitish')
    name = params.get('name')
    body = params.get('body')
    draft = params.get('draft')
    prerelease = params.get('prerelease')

    requires_update=False
    for attr_name in ['tag_name', 'target_commitish', 'name', 'body', 'draft', 'prerelease']:
        if getattr(release, attr_name) != module.params.get(attr_name):
            requires_update=True

    if requires_update:
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
            token=dict(required=True, no_log=True),
            action=dict(choices=['latest_release'], default=None),
            state=dict(choices=['absent', 'present'], default=None),
            body=dict(default=None),
            name=dict(default=None),
            tag_name=dict(required=False),
            target_commitish=dict(required=False),
            draft=dict(required=False, type='bool', default=False),
            prerelease=dict(type='bool', default=False)
        ),
        mutually_exclusive=[
            ['state', 'action'],
        ],
        required_if=[
            ['state', 'present', ['tag_name', 'target_commitish']],
            ['state', 'absent', ['tag_name']],
        ],
        supports_check_mode=False
    )

    if not HAS_GITHUB_API:
        module.fail_json(msg='Missing requried github3 module (check docs or install with: pip install github3)')

    repo = module.params['repo']
    user = module.params['user']
    login_token = module.params['token']
    action = module.params['action']
    state = module.params['state']

    # login to github
    try:
        gh = github3.login(token=str(login_token))
        # test if we're actually logged in
        gh.me()
    except github3.AuthenticationFailed:
        e = get_exception()
        module.fail_json(msg='Failed to connect to Github: %s' % e)

    repository = gh.repository(str(user), str(repo))

    if not repository:
        module.fail_json(msg="Repository %s/%s doesn't exist" % (user, repo))

    if action == 'latest_release':
        fact_finder(module, repository)

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
                    module.exit_json(changed=True)
                else:
                    module.fail_json(msg="Failed to delete release")

        elif state == 'present':
            if isinstance(release, github3.null.NullObject):
                release = create_release(module, repository)
                module.exit_json(changed=True, release=release.as_dict())

            else:
                update = update_release(module, release)
                if update is None:
                    module.exit_json(changed=False, release=release.as_dict())
                elif update:
                    module.exit_json(changed=True, release=release.as_dict())
                else:
                    module.fail_json(msg="Failed to update release")

        else:
            module.fail_json(msg="No action or state provided")

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
