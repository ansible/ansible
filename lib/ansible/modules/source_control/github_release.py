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
  action:
    required: true
    description:
      - Action to perform
    choices: [ 'latest_release', 'create_release' ]
  tag:
    required: false
    description:
      - Tag name when creating a release. Required when using create_release.
    version_added: 2.4
  target:
    required: false
    description:
      - Target of release when creating a release
    version_added: 2.4
  name:
    required: false
    description:
      - Name of release when creating a release
    version_added: 2.4
  body:
    required: false
    description:
      - Description of the release when creating a release
    version_added: 2.4
  draft:
    required: false
    description:
      - Sets if the release is a draft or not. (boolean)
    default: false
    version_added: 2.4
    choices: ['True', 'False']
  prerelease:
    required: false
    description:
      - Sets if the release is a prerelease or not. (boolean)
    default: false
    version_added: 2.4
    choices: ['True', 'False']

author:
    - "Adrian Moisey (@adrianmoisey)"
requirements:
    - "github3.py >= 1.0.0a3"
'''

EXAMPLES = '''
- name: Get latest release of testuser/testrepo
  github:
    token: tokenabc1234567890
    user: testuser
    repo: testrepo
    action: latest_release

- name: Create a new release
  github:
    token: tokenabc1234567890
    user: testuser
    repo: testrepo
    action: create_release
    tag: test
    target: master
    name: My Release
    body: Some description
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


def main():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(required=True),
            user=dict(required=True),
            token=dict(required=True, no_log=True),
            action=dict(
                required=True, choices=['latest_release', 'create_release']),
            tag=dict(type='str'),
            target=dict(type='str'),
            name=dict(type='str'),
            body=dict(type='str'),
            draft=dict(type='bool', default=False),
            prerelease=dict(type='bool', default=False),
        ),
        supports_check_mode=True
    )

    if not HAS_GITHUB_API:
        module.fail_json(msg='Missing required github3 module (check docs or '
                             'install with: pip install github3.py==1.0.0a4)')

    repo = module.params['repo']
    user = module.params['user']
    login_token = module.params['token']
    action = module.params['action']
    tag = module.params.get('tag')
    target = module.params.get('target')
    name = module.params.get('name')
    body = module.params.get('body')
    draft = module.params.get('draft')
    prerelease = module.params.get('prerelease')

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
        release = repository.latest_release()
        if release:
            module.exit_json(tag=release.tag_name)
        else:
            module.exit_json(tag=None)

    if action == 'create_release':
        if tag is None:
            module.fail_json(msg="Specify tag in order to create a release.")
        release_exists = repository.release_from_tag(tag)
        if release_exists:
            module.exit_json(
                skipped=True, msg="Release for tag %s already exists." % tag)

        release = repository.create_release(
            tag, target, name, body, draft, prerelease)
        if release:
            module.exit_json(tag=release.tag_name)
        else:
            module.exit_json(tag=None)

from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
