#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: github_deploy_key
version_added: "2.4"
author: "Ali (@bincyber)"
short_description: Manages deploy keys for GitHub repositories.
description:
  - "Adds or removes deploy keys for GitHub repositories. Supports authentication using username and password,
  username and password and 2-factor authentication code (OTP), OAuth2 token, or personal access token."
options:
  owner:
    description:
      - The name of the individual account or organization that owns the GitHub repository.
    required: true
    aliases: [ 'account', 'organization' ]
  repo:
    description:
      - The name of the GitHub repository.
    required: true
    aliases: [ 'repository' ]
  name:
    description:
      - The name for the deploy key.
    required: true
    aliases: [ 'title', 'label' ]
  key:
    description:
      - The SSH public key to add to the repository as a deploy key.
    required: true
  read_only:
    description:
      - If C(true), the deploy key will only be able to read repository contents. Otherwise, the deploy key will be able to read and write.
    type: bool
    default: 'yes'
  state:
    description:
      - The state of the deploy key.
    default: "present"
    choices: [ "present", "absent" ]
  force:
    description:
      - If C(true), forcefully adds the deploy key by deleting any existing deploy key with the same public key or title.
    type: bool
    default: 'no'
  username:
    description:
      - The username to authenticate with.
  password:
    description:
      - The password to authenticate with. A personal access token can be used here in place of a password.
  token:
    description:
      - The OAuth2 token or personal access token to authenticate with. Mutually exclusive with I(password).
  otp:
    description:
      - The 6 digit One Time Password for 2-Factor Authentication. Required together with I(username) and I(password).
    aliases: ['2fa_token']
requirements:
   - python-requests
notes:
   - "Refer to GitHub's API documentation here: https://developer.github.com/v3/repos/keys/."
'''

EXAMPLES = '''
# add a new read-only deploy key to a GitHub repository using basic authentication
- github_deploy_key:
    owner: "johndoe"
    repo: "example"
    name: "new-deploy-key"
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDAwXxn7kIMNWzcDfou..."
    read_only: yes
    username: "johndoe"
    password: "supersecretpassword"

# remove an existing deploy key from a GitHub repository
- github_deploy_key:
    owner: "johndoe"
    repository: "example"
    name: "new-deploy-key"
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDAwXxn7kIMNWzcDfou..."
    force: yes
    username: "johndoe"
    password: "supersecretpassword"
    state: absent

# add a new deploy key to a GitHub repository, replace an existing key, use an OAuth2 token to authenticate
- github_deploy_key:
    owner: "johndoe"
    repository: "example"
    name: "new-deploy-key"
    key: "{{ lookup('file', '~/.ssh/github.pub') }}"
    force: yes
    token: "ABAQDAwXxn7kIMNWzcDfo..."

# re-add a deploy key to a GitHub repository but with a different name
- github_deploy_key:
    owner: "johndoe"
    repository: "example"
    name: "replace-deploy-key"
    key: "{{ lookup('file', '~/.ssh/github.pub') }}"
    username: "johndoe"
    password: "supersecretpassword"

# add a new deploy key to a GitHub repository using 2FA
- github_deploy_key:
    owner: "johndoe"
    repo: "example"
    name: "new-deploy-key-2"
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDAwXxn7kIMNWzcDfou..."
    username: "johndoe"
    password: "supersecretpassword"
    otp: 123456
'''

RETURN = '''
msg:
    description: the status message describing what occurred
    returned: always
    type: string
    sample: "Deploy key added successfully"

http_status_code:
    description: the HTTP status code returned by the GitHub API
    returned: failed
    type: int
    sample: 400

error:
    description: the error message returned by the GitHub API
    returned: failed
    type: string
    sample: "key is already in use"

id:
    description: the key identifier assigned by GitHub for the deploy key
    returned: changed
    type: int
    sample: 24381901
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url


class GithubDeployKey(object):
    def __init__(self, module=None, url=None, state=None, username=None, password=None, token=None, otp=None):
        self.module = module
        self.url = url
        self.state = state
        self.username = username
        self.password = password
        self.token = token
        self.otp = otp
        self.timeout = 5
        self.auth = None
        self.headers = None

        if username is not None and password is not None:
            self.module.params['url_username'] = module.params['username']
            self.module.params['url_password'] = module.params['password']
            self.module.params['force_basic_auth'] = True
            if self.otp is not None:
                self.headers = {"X-GitHub-OTP": self.otp}
        else:
            self.headers = {"Authorization": "token {}".format(self.token)}

    def get_existing_key(self, key, title, force):
        resp, info = fetch_url(self.module, self.url, headers=self.headers, method="GET")

        status_code = info["status"]

        if status_code == 200:
            response_body = json.loads(resp.read())

            if response_body:
                for i in response_body:
                    existing_key_id = str(i["id"])
                    if i["key"].split() == key.split()[:2]:
                        return existing_key_id
                    elif i['title'] == title and force:
                        return existing_key_id
            else:
                if self.state == 'absent':
                    self.module.exit_json(changed=False, msg="Deploy key does not exist")
                else:
                    return None
        elif status_code == 401:
            self.module.fail_json(msg="Failed to connect to github.com due to invalid credentials", http_status_code=status_code)
        elif status_code == 404:
            self.module.fail_json(msg="GitHub repository does not exist", http_status_code=status_code)
        else:
            self.module.fail_json(msg="Failed to retrieve existing deploy keys", http_status_code=status_code)

    def add_new_key(self, request_body):
        resp, info = fetch_url(self.module, self.url, data=json.dumps(request_body), headers=self.headers, method="POST")

        status_code = info["status"]

        if status_code == 201:
            response_body = json.loads(resp.read())
            key_id = response_body["id"]
            self.module.exit_json(changed=True, msg="Deploy key successfully added", id=key_id)
        elif status_code == 401:
            self.module.fail_json(msg="Failed to connect to github.com due to invalid credentials", http_status_code=status_code)
        elif status_code == 404:
            self.module.fail_json(msg="GitHub repository does not exist", http_status_code=status_code)
        elif status_code == 422:
            self.module.exit_json(changed=False, msg="Deploy key already exists")
        else:
            err = info["body"]
            self.module.fail_json(msg="Failed to add deploy key", http_status_code=status_code, error=err)

    def remove_existing_key(self, key_id):
        resp, info = fetch_url(self.module, self.url + "/{}".format(key_id), headers=self.headers, method="DELETE")

        status_code = info["status"]

        if status_code == 204:
            if self.state == 'absent':
                self.module.exit_json(changed=True, msg="Deploy key successfully deleted", id=key_id)
        else:
            self.module.fail_json(msg="Failed to delete existing deploy key", id=key_id, http_status_code=status_code)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            owner=dict(required=True, type='str', aliases=['account', 'organization']),
            repo=dict(required=True, type='str', aliases=['repository']),
            name=dict(required=True, type='str', aliases=['title', 'label']),
            key=dict(required=True, type='str'),
            read_only=dict(required=False, type='bool', default=True),
            state=dict(default='present', choices=['present', 'absent']),
            force=dict(required=False, type='bool', default=False),
            username=dict(required=False, type='str'),
            password=dict(required=False, type='str', no_log=True),
            otp=dict(required=False, type='int', aliases=['2fa_token'], no_log=True),
            token=dict(required=False, type='str', no_log=True)
        ),
        mutually_exclusive=[
            ['password', 'token']
        ],
        required_together=[
            ['username', 'password'],
            ['otp', 'username', 'password']
        ],
        required_one_of=[
            ['username', 'token']
        ],
        supports_check_mode=True,
    )

    owner = module.params['owner']
    repo = module.params['repo']
    name = module.params['name']
    key = module.params['key']
    state = module.params['state']
    read_only = module.params.get('read_only', True)
    force = module.params.get('force', False)
    username = module.params.get('username', None)
    password = module.params.get('password', None)
    token = module.params.get('token', None)
    otp = module.params.get('otp', None)

    GITHUB_API_URL = "https://api.github.com/repos/{}/{}/keys".format(owner, repo)

    deploy_key = GithubDeployKey(module, GITHUB_API_URL, state, username, password, token, otp)

    if module.check_mode:
        key_id = deploy_key.get_existing_key(key, name, force)
        if state == "present" and key_id is None:
            module.exit_json(changed=True)
        elif state == "present" and key_id is not None:
            module.exit_json(changed=False)

    # to forcefully modify an existing key, the existing key must be deleted first
    if state == 'absent' or force:
        key_id = deploy_key.get_existing_key(key, name, force)

        if key_id is not None:
            deploy_key.remove_existing_key(key_id)

    deploy_key.add_new_key({"title": name, "key": key, "read_only": read_only})


if __name__ == '__main__':
    main()
