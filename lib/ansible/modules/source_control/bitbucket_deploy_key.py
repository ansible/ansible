#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = '''
---
module: bitbucket_deploy_key
version_added: "2.8"
author: "Ali (@bincyber)"
short_description: Manages deploy keys for BitBucket repositories.
description:
  - "Adds or removes deploy keys for Bitbucket repositories. Supports authentication to the BitBucket API
  using username and password."
options:
  account_name:
    description:
      - The name of the team or individual account that owns the BitBucket repository.
    required: True
    type: str
    aliases: [ 'account', 'organization' ]
  repository:
    description:
      - The name of the BitBucket repository.
    required: True
    type: str
    aliases: [ 'repo' ]
  label:
    description:
      - The user-visible label on the deploy key.
    required: True
    type: str
  key:
    description:
      - The SSH public key to add to the repository as a deploy key.
    required: True
    type: str
  state:
    description:
      - The state of the deploy key.
    required: False
    default: "present"
    choices: [ "present", "absent" ]
    type: str
  force:
    description:
      - If C(true), forcefully adds the deploy key by deleting any existing deploy key with the same public key or title.
    required: False
    default: False
    choices: [ True, False ]
    type: bool
  username:
    description:
      - The username to authenticate with.
    required: True
    type: str
  password:
    description:
      - The password to authenticate with. You can use app passwords here.
    required: True
    type: str
requirements:
   - python-requests
notes:
    - "Refer to BitBucket's API documentation here: U(https://confluence.atlassian.com/bitbucket/deploy-keys-resource-296095243.html)"
'''

EXAMPLES = '''
# add a new deploy key to a BitBucket repository
- bitbucket_deploy_key:
    account_name: "johndoe"
    repository: "example"
    label: "new-deploy-key"
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDAwXxn7kIMNWzcDfou..."
    username: "johndoe"
    password: "supersecretpassword"

# remove an existing deploy key from a BitBucket repository
- bitbucket_deploy_key:
    account_name: "johndoe"
    repository: "example"
    label: "new-deploy-key"
    key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDAwXxn7kIMNWzcDfou..."
    force: yes
    username: "johndoe"
    password: "supersecretpassword"
    state: absent

# add a new deploy key to a BitBucket repository, replace an existing key
- bitbucket_deploy_key:
    account_name: "johndoe"
    repository: "example"
    label: "new-deploy-key"
    key: "{{ lookup('file', '~/.ssh/bitbucket.pub') }}"
    force: yes
    username: "johndoe"
    password: "supersecretpassword"

# re-add a deploy key to a BitBucket repository but with a different label
- bitbucket_deploy_key:
    account_name: "johndoe"
    repository: "example"
    label: "replace-deploy-key"
    key: "{{ lookup('file', '~/.ssh/bitbucket.pub') }}"
    username: "johndoe"
    password: "supersecretpassword"
'''

RETURN = '''
msg:
    description: the status message describing what occurred
    returned: always
    type: str
    sample: "Deploy key added successfully"

http_status_code:
    description: the HTTP status code returned by the BitBucket API
    returned: failed
    type: int
    sample: 400

pk:
    description: the key identifier assigned by BitBucket for the deploy key
    returned: changed
    type: int
    sample: 243819
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlencode
import json


class BitBucketDeployKey(object):
    def __init__(self, module=None, url=None, state=None):
        self.module = module
        self.url = url
        self.state = state

    def get_existing_key(self, label, key, force):
        resp, info = fetch_url(self.module, self.url, method="GET")

        status_code = info["status"]

        if status_code == 200:
            response_body = json.loads(resp.read())

            if response_body:
                for i in response_body:
                    existing_key = str(i["pk"])
                    if i["key"] == key:
                        return existing_key
                    elif i['label'] == label and force:
                        return existing_key
            else:
                if self.state == 'absent':
                    self.module.exit_json(changed=False, msg="Deploy key does not exist")
                else:
                    return None
        elif status_code == 401:
            self.module.fail_json(msg="Failed to connect to bitbucket.org due to invalid credentials", http_status_code=status_code)
        elif status_code == 404:
            self.module.fail_json(msg="BitBucket repository does not exist", http_status_code=status_code)
        else:
            self.module.fail_json(msg="Failed to retrieve existing deploy keys", http_status_code=status_code)

    def add_new_key(self, label, key):
        request_body = {
            "label": label,
            "key": key
        }

        resp, info = fetch_url(self.module, self.url, data=urlencode(request_body), method="POST")

        status_code = info["status"]

        if status_code == 200:
            response_body = json.loads(resp.read())
            key_id = response_body["pk"]
            self.module.exit_json(changed=True, msg="Deploy key successfully added", pk=key_id)
        elif status_code == 400:
            existing_key_msg = "Someone has already added that access key to this repository"
            if existing_key_msg in info["body"]:
                self.module.exit_json(changed=False, msg="Deploy key already exists")
            else:
                self.module.fail_json(msg="Bad request", error=info["body"], data=json.dumps(request_body))
        elif status_code == 401:
            self.module.fail_json(msg="Failed to connect to bitbucket.org due to invalid credentials", http_status_code=status_code)
        elif status_code == 404:
            self.module.fail_json(msg="BitBucket repository does not exist", http_status_code=status_code)
        else:
            self.module.fail_json(msg="Failed to add deploy key", http_status_code=status_code, error=info["body"])

    def remove_existing_key(self, pk):
        resp, info = fetch_url(self.module, self.url + '/' + pk, method="DELETE")

        status_code = info["status"]

        if status_code == 204:
            if self.state == 'absent':
                self.module.exit_json(changed=True, msg="Deploy key successfully deleted", pk=pk)
        elif status_code == 401:
            self.module.fail_json(msg="Failed to connect to bitbucket.org due to invalid credentials", http_status_code=status_code)
        elif status_code == 404:
            self.module.fail_json(msg="BitBucket repository does not exist", http_status_code=status_code)
        else:
            self.module.fail_json(msg="Failed to delete existing deploy key", pk=pk, http_status_code=status_code)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            account_name=dict(required=True, type='str', aliases=['account', 'organization']),
            repository=dict(required=True, type='str', aliases=['repo']),
            label=dict(required=True, type='str'),
            key=dict(required=True, type='str'),
            state=dict(default='present', choices=['present', 'absent']),
            force=dict(required=False, type='bool', default=False, choices=[True, False]),
            username=dict(required=True, type='str'),
            password=dict(required=True, type='str', no_log=True),
        ),
        required_together=[
            ['username', 'password']
        ],
        supports_check_mode=True,
    )

    account_name = module.params['account_name']
    repository = module.params['repository']
    label = module.params['label']
    key = module.params['key']
    state = module.params['state']
    force = module.params.get('force', False)

    module.params['url_username'] = module.params['username']
    module.params['url_password'] = module.params['password']
    module.params['force_basic_auth'] = True

    BITBUCKET_API_URL = "https://api.bitbucket.org/1.0/repositories/{0}/{1}/deploy-keys".format(account_name, repository)

    deploy_key = BitBucketDeployKey(module, BITBUCKET_API_URL, state)

    if module.check_mode:
        pk = deploy_key.get_existing_key(label, key, force)
        if state == "present" and pk is None:
            module.exit_json(changed=True)
        elif state == "present" and pk is not None:
            module.exit_json(changed=False)

    # to forcefully modify an existing key, the existing key must be deleted first
    if state == 'absent' or force:
        pk = deploy_key.get_existing_key(label, key, force)

        if pk is not None:
            deploy_key.remove_existing_key(pk)

    deploy_key.add_new_key(label, key)


if __name__ == '__main__':
    main()
