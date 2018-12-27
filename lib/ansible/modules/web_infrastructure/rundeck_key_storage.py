#!/usr/bin/python
# -*- coding: utf-8 -*-

# Ansible module to manage rundeck projects
# (c) 2018, Amine CHIKOUCHE <amine.chikouche@fitbrain.guru>
# Sponsored by Bnp Paribas CIB. https://group.bnpparibas/en/group/activities/corporate-institutional-banking
#
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
version_added: "3.0.9"
rundeck_api_version: "27"
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
    url:
        description:
            - Sets the rundeck instance URL.
        required: True
    api_version:
        description:
            - Sets the API version used by module.
            - API version must be at least 14.
        default: 14
    token:
        description:
            - Sets the token to authenticate against Rundeck API.
        required: True
'''

EXAMPLES = '''
- name: Create a rundeck private key
  rundeck_key_storage:
    type: private_key
    path: "myproject/rundeck_private_key"
    data: "{{ data }}"
    api_version: 27
    url: "https://rundeck.example.org"
    token: "mytoken"
    state: present
'''

RETURN = '''

????????????

rundeck_response:
    description: Rundeck response when a failure occurs
    returned: failed
    type: str
before:
    description: dictionnary containing project informations before modification
    returned: success
    type: dict
after:
    description: dictionnary containing project informations after modification
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

    def request_rundeck_api(self, query, content_type, accept, data, method):
        resp, info = fetch_url(self.module,
                               "%s/api/%d/%s" % (self.module.params["url"], self.module.params["api_version"], query),
                               data=json.dumps(data),
                               method=method,
                               headers={
                                   "Content-Type": content_type,
                                   "Accept": accept,
                                   "X-Rundeck-Auth-Token": self.module.params["token"]
                               })
        self.handle_http_code_if_needed(info)
        if resp is not None:
            resp = resp.read()
            if resp != "":
                try:
                    json_resp = json.loads(resp)
                    return json_resp, info
                except ValueError as e:
                    self.module.fail_json(msg="Rundeck response was not a valid JSON. Exception was: %s. "
                                              "Object was: %s" % (to_native(e), resp))
        return resp, info

    def create_request_rundeck_api(self, query, content_type, data, method):
        resp, info = fetch_url(self.module,
                               "%s/api/%d/%s" % (
                                   self.module.params["url"], self.module.params["api_version"], query),
                               data=json.dumps(data),
                               method=method,
                               headers={
                                   "Content-Type": content_type,
                                   "X-Rundeck-Auth-Token": self.module.params["token"]
                               })

        self.handle_http_code_if_needed(info)
        if resp is not None:
            resp = resp.read()
            if resp != "":
                try:
                    json_resp = json.loads(resp)
                    return json_resp, info
                except ValueError as e:
                    self.module.fail_json(msg="Rundeck response was not a valid JSON. Exception was: %s. "
                                              "Object was: %s" % (to_native(e), resp))
        return resp, info

    def key_storage_facts(self):
        resp, info = self.request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                              "application/json",
                                              "application/json",
                                              None,
                                              "GET")
        return resp

    def create_or_update_key(self):
        global content_type

        if self.module.params["type"] == "private_key":
            content_type = "application/octet-stream"
        if self.module.params["type"] == "public_key":
            content_type = "application/pgp-keys"
        if self.module.params["type"] == "password":
            content_type = "x-rundeck-data-password"

        facts = self.key_storage_facts()
        if facts is None:
            # If in check mode don't create key, simulate a fake key creation
            if self.module.check_mode:
                self.module.exit_json(changed=True, before={}, after={"name": self.module.params["name"]})

            # create a key
            resp, info = self.create_request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                                         content_type,
                                                         self.module.params["data"],
                                                         "POST")

            if info["status"] == 201:
                self.module.exit_json(changed=True, before={}, after=self.key_storage_facts())
            else:
                self.module.fail_json(msg="Unhandled HTTP status %d, please report the bug" % info["status"],
                                      before={}, after=self.key_storage_facts())
        else:
            # update existing key  query, content_type, accept, data, method
            resp, info = self.create_request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                                         content_type,
                                                         self.module.params["data"],
                                                         "PUT")

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
                self.request_rundeck_api("storage/keys/%s" % self.module.params["path"],
                                         "application/json",
                                         "application/json",
                                         None,
                                         "DELETE")

            self.module.exit_json(changed=True, before=facts, after={})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            type=dict(type='str', choices=['private_key', 'public_key', 'password'], default='private_key'),
            path=dict(required=True, type='str'),
            data=dict(required=True, type='str', no_log=True),
            url=dict(required=True, type='str'),
            api_version=dict(type='int', default=14),
            token=dict(required=True, type='str', no_log=True),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            check_mode=dict(type='str', choices=['yes', 'no'], default='no')
        ),
        supports_check_mode=False
    )

    if module.params["check_mode"] == 'yes':
        module.check_mode = True

    if module.params["api_version"] < 14:
        module.fail_json(msg="API version should be at least 14")

    rundeck = RundeckKeyStorageManager(module)
    if module.params['state'] == 'present':
        rundeck.create_or_update_key()
    elif module.params['state'] == 'absent':
        rundeck.remove_key()


if __name__ == '__main__':
    main()
