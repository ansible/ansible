#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Loic Blot <loic.blot@unix-experience.fr>
# Sponsored by Infopro Digital. http://www.infopro-digital.com/
# Sponsored by E.T.A.I. http://www.etai.fr/
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: rundeck_acl_policy

short_description: Manage Rundeck ACL policies.
description:
    - Create, update and remove Rundeck ACL policies through HTTP API.
version_added: "2.4"
author: "Loic Blot (@nerzhul)"
options:
    state:
        description:
            - Create or remove Rundeck project.
        choices: ['present', 'absent']
        default: 'present'
    name:
        description:
            - Sets the project name.
        required: True
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
    project:
        description:
            - Sets the project which receive the ACL policy.
            - If unset, it's a system ACL policy.
    policy:
        description:
            - Sets the ACL policy content.
            - ACL policy content is a YAML object as described in http://rundeck.org/docs/man5/aclpolicy.html.
            - It can be a YAML string or a pure Ansible inventory YAML object.
'''

EXAMPLES = '''
- name: Create or update a rundeck ACL policy in project Ansible
  rundeck_acl_policy:
    name: "Project_01"
    api_version: 18
    url: "https://rundeck.example.org"
    token: "mytoken"
    state: present
    project: "Ansible"
    policy:
      description: "my policy"
      context:
        application: rundeck
      for:
        project:
          - allow: read
      by:
        group: "build"

- name: Remove a rundeck system policy
  rundeck_acl_policy:
    name: "Project_02"
    url: "https://rundeck.example.org"
    token: "mytoken"
    state: absent
'''

RETURN = '''
rundeck_response:
    description: Rundeck response when a failure occurs.
    returned: failed
    type: string
before:
    description: dictionnary containing ACL policy informations before modification.
    returned: success
    type: dict
after:
    description: dictionnary containing ACL policy informations after modification.
    returned: success
    type: dict
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
import json


class RundeckACLManager:
    def __init__(self, module):
        self.module = module

    def handle_http_code_if_needed(self, infos):
        if infos["status"] == 403:
            self.module.fail_json(msg="Token not allowed. Please ensure token is allowed or has the correct "
                                      "permissions.", rundeck_response=infos["body"])
        elif infos["status"] >= 500:
            self.module.fail_json(msg="Fatal Rundeck API error.", rundeck_response=infos["body"])

    def request_rundeck_api(self, query, data=None, method="GET"):
        resp, info = fetch_url(self.module,
                               "%s/api/%d/%s" % (self.module.params["url"], self.module.params["api_version"], query),
                               data=json.dumps(data),
                               method=method,
                               headers={
                                   "Content-Type": "application/json",
                                   "Accept": "application/json",
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
                                              "Object was: %s" % (str(e), resp))
        return resp, info

    def get_acl(self):
        resp, info = self.request_rundeck_api("system/acl/%s.aclpolicy" % self.module.params["name"])
        return resp

    def create_or_update_acl(self):
        facts = self.get_acl()
        if facts is None:
            # If in check mode don't create project, simulate a fake project creation
            if self.module.check_mode:
                self.module.exit_json(changed=True, before={}, after=self.module.params["policy"])

            _, info = self.request_rundeck_api("system/acl/%s.aclpolicy" % self.module.params["name"],
                                               method="POST",
                                               data={"contents": self.module.params["policy"]})

            if info["status"] == 201:
                self.module.exit_json(changed=True, before={}, after=self.get_acl())
            elif info["status"] == 400:
                self.module.fail_json(msg="Unable to validate acl %s. Please ensure it's a valid ACL" %
                                          self.module.params["name"])
            elif info["status"] == 409:
                self.module.fail_json(msg="ACL %s already exists" % self.module.params["name"])
            else:
                self.module.fail_json(msg="Unhandled HTTP status %d, please report the bug" % info["status"],
                                      before={}, after=self.get_acl())
        else:
            if facts["contents"] == self.module.params["policy"]:
                self.module.exit_json(changed=False, before=facts, after=facts)

            if self.module.check_mode:
                self.module.exit_json(changed=True, before=facts, after=facts)

            _, info = self.request_rundeck_api("system/acl/%s.aclpolicy" % self.module.params["name"],
                                               method="PUT",
                                               data={"contents": self.module.params["policy"]})

            if info["status"] == 200:
                self.module.exit_json(changed=True, before=facts, after=self.get_acl())
            elif info["status"] == 400:
                self.module.fail_json(msg="Unable to validate acl %s. Please ensure it's a valid ACL" %
                                          self.module.params["name"])
            elif info["status"] == 404:
                self.module.fail_json(msg="ACL %s doesn't exists. Cannot update." % self.module.params["name"])

    def remove_acl(self):
        facts = self.get_acl()
        if facts is None:
            self.module.exit_json(changed=False, before={}, after={})
        else:
            # If not in check mode, remove the project
            if not self.module.check_mode:
                self.request_rundeck_api("system/acl/%s.aclpolicy" % self.module.params["name"], method="DELETE")
            self.module.exit_json(changed=True, before=facts, after={})


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            url=dict(required=True, type='str'),
            api_version=dict(type='int', default=14),
            token=dict(required=True, type='str', no_log=True),
            policy=dict(type='str'),
            project=dict(type='str'),
        ),
        required_if=[
            ['state', 'present', ['policy']],
        ],
        supports_check_mode=True
    )

    if module.params["api_version"] < 14:
        module.fail_json(msg="API version should be at least 14")

    rundeck = RundeckACLManager(module)
    if module.params['state'] == 'present':
        rundeck.create_or_update_acl()
    elif module.params['state'] == 'absent':
        rundeck.remove_acl()

if __name__ == '__main__':
    main()
