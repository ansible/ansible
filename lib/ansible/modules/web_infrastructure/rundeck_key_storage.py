#!/usr/bin/python
# -*- coding: utf-8 -*-

# Ansible module to manage rundeck projects
# (c) 2019, Amine CHIKOUCHE <amine.chikouche@fitbrain.guru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rundeck_key_storage

short_description: Manage Rundeck key storage.
description:
    - Upload, update, delete Rundeck key storage through HTTP API.
version_added: "2.8"
author: "Amine CHIKOUCHE (@aminx4)"
options:
    type:
        description:
            - set the type of the key
        choices: ['private_key', 'public_key', 'password']
        required: True
    path:
        description:
            - set the path after /storage/keys/[PATH]/[FILENAME]
        required: True
    data:
        description:
            - set the key data
    api_version:
        description:
            - Sets the API version used by module.
            - API version must be at least 14.
        default: 14
    url:
        description:
            - Sets the rundeck instance URL.
        required: True
    token:
        description:
            - Sets the token to authenticate against Rundeck API.
        required: True
    state:
        description:
            - create, update or remove a key
        choices: ['present', 'absent']
        default: present
'''

EXAMPLES = '''

- name: Create a rundeck private key
  rundeck_key_storage:
    type: 'private_key'
    path: "myProject/rundeck_private_key"
    data: 'data'
    api_version: 27
    url: "http://127.0.0.1:4440"
    token: "uN7Z2VmnhNc4ANKCHYoKMxicsZWx3AZj"
    state: "present"

- name: Create a rundeck public key
  rundeck_key_storage:
    type: 'public_key'
    path: "myProject/rundeck_public_key"
    data: 'data'
    api_version: 27
    url: "http://127.0.0.1:4440"
    token: "uN7Z2VmnhNc4ANKCHYoKMxicsZWx3AZj"
    state: "present"

- name: Create a rundeck password
  rundeck_key_storage:
    type: 'password'
    path: "myProject/password"
    data: 'data'
    api_version: 27
    url: "http://127.0.0.1:4440"
    token: "uN7Z2VmnhNc4ANKCHYoKMxicsZWx3AZj"
    state: "present"

- name: delete a rundeck private key
  rundeck_key_storage:
    type: 'private_key'
    path: "myProject/rundeck_private_key"
    data: 'data'
    api_version: 27
    url: "http://127.0.0.1:4440"
    token: "uN7Z2VmnhNc4ANKCHYoKMxicsZWx3AZj"
    state: "absent"

- name: delete a rundeck password
  rundeck_key_storage:
    type: 'password'
    path: "myProject/password"
    data: 'data'
    api_version: 27
    url: "http://127.0.0.1:4440"
    token: "uN7Z2VmnhNc4ANKCHYoKMxicsZWx3AZj"
    state: "absent"

- name: delete a rundeck public key
  rundeck_key_storage:
    type: 'public_key'
    path: "myProject/rundeck_public_key"
    data: 'data'
    api_version: 27
    url: "http://127.0.0.1:4440"
    token: "uN7Z2VmnhNc4ANKCHYoKMxicsZWx3AZj"
    state: "absent"

'''

RETURN = '''

rundeck_response:
    description: Rundeck response when a failure occurs
    returned: failed
    type: str
before:
    description: dictionnary containing key informations before modification
    returned: success
    type: dict
after:
    description: dictionnary containing key informations after modification
    returned: success
    type: dict
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible.module_utils.urls import fetch_url
import json


class RundeckKeyStorageManager(object):

    def __init__(self, module):
        self.module = module

    def handle_http_code_if_needed(self, infos):
        if infos["status"] == 403:
            self.module.fail_json(msg="Token not allowed. Please ensure token is allowed or has the correct "
                                      "permissions.", rundeck_response=infos["body"])
        elif infos["status"] >= 500:
            self.module.fail_json(msg="Fatal Rundeck API error.", rundeck_response=infos["body"])

    def request_rundeck_api(self, query, headers, method, data=None):
        resp, info = fetch_url(self.module,
                               "%s/api/%d/%s" % (self.module.params["url"], self.module.params["api_version"], query),
                               data=json.dumps(data),
                               method=method,
                               headers=headers,
                               force=True)

        self.handle_http_code_if_needed(info)
        if resp is None or info["status"] == 204:
            return resp, info
        else:
            resp_read = resp.read()
            if resp_read != "":
                try:
                    json_resp = json.loads(resp_read)
                    return json_resp, info
                except ValueError as e:
                    self.module.fail_json(msg="Rundeck response was not a valid JSON. Exception was: %s. "
                                              "Object was: %s" % (to_native(e), resp_read))
            return resp, info

    def key_storage_facts(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Rundeck-Auth-Token": self.module.params["token"]
        }
        resp, info = self.request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                              headers,
                                              "GET")
        return resp

    def create_or_update_key(self):
        global content_type

        if self.module.params["type"] == "private_key":
            content_type = "application/octet-stream"
        elif self.module.params["type"] == "public_key":
            content_type = "application/pgp-keys"
        elif self.module.params["type"] == "password":
            content_type = "x-rundeck-data-password"

        facts = self.key_storage_facts()
        headers = {
            "Content-Type": content_type,
            "X-Rundeck-Auth-Token": self.module.params["token"]
        }
        if facts is None:
            # If in check mode don't create key, simulate a fake key creation
            if self.module.check_mode:
                self.module.exit_json(changed=True, before={}, after={"path": self.module.params["path"]})

            # create a key
            resp, info = self.request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                                  headers,
                                                  "POST",
                                                  self.module.params["data"])

            if info["status"] == 201:
                self.module.exit_json(changed=True, before={}, after=self.key_storage_facts())
            else:
                self.module.fail_json(msg="Unhandled HTTP status %d, please report the bug" % info["status"],
                                      before={}, after=self.key_storage_facts())
        else:
            # update existing key  query, content_type, accept, data, method
            resp, info = self.request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                                  headers,
                                                  "PUT",
                                                  self.module.params["data"])

            if info["status"] == 200:
                self.module.exit_json(changed=True, before={}, after=self.key_storage_facts())

            else:
                self.module.fail_json(msg="Unhandled HTTP status %d, please report the bug" % info["status"],
                                      before={}, after=facts)

    def remove_key(self):
        facts = self.key_storage_facts()
        if facts is None:
            self.module.exit_json(changed=False, before={}, after={})
        else:
            # If not in check mode, remove the project
            if not self.module.check_mode:
                headers = {
                    "Content-Type": "application/json",
                    "X-Rundeck-Auth-Token": self.module.params["token"]
                }
                resp, info = self.request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                                      headers,
                                                      "DELETE")
                if info["status"] == 200 or info["status"] == 204:
                    self.module.exit_json(changed=True, before=facts, after={})
                if info["status"] == 404:
                    self.module.exit_json(changed=False, before=facts, after={})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            type=dict(required=True, type='str', choices=['private_key', 'public_key', 'password']),
            path=dict(required=True, type='str'),
            data=dict(type='str', no_log=True),
            url=dict(required=True, type='str'),
            api_version=dict(type='int', default=14),
            token=dict(required=True, type='str', no_log=True),
            state=dict(type='str', choices=['present', 'absent'], default='present')
        ),
        supports_check_mode=True
    )

    if module.params["api_version"] < 14:
        module.fail_json(msg="API version should be at least 14")

    rundeck = RundeckKeyStorageManager(module)
    if module.params['state'] == 'present':
        rundeck.create_or_update_key()
    elif module.params['state'] == 'absent':
        rundeck.remove_key()


if __name__ == '__main__':
    main()
