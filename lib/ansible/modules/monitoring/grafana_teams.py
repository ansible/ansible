#!/usr/bin/python
# -*- coding: utf-8 -*-
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.1'
}

DOCUMENTATION = '''
---
module: grafana_teams
author:
  - Rémi REY (@rrey)
version_added: "2.10"
short_description: Manage Grafana Teams
description:
  - Create/update/delete Grafana Teams through API.
options:
  url:
    description:
      - The Grafana URL.
    required: true
    type: str
  name:
    description:
      - The name of the Grafana Team.
    required: true
    type: str
  email:
    description:
      - The mail address associated with the Team.
    required: true
    type: str
  url_username:
    description:
      - The Grafana user for API authentication.
    default: admin
    type: str
    aliases: [ grafana_user ]
  url_password:
    description:
      - The Grafana password for API authentication.
    default: admin
    type: str
    aliases: [ grafana_password ]
  grafana_api_key:
    description:
      - The Grafana API key.
      - If set, C(url_username) and C(url_password) will be ignored.
    type: str
  members:
    description:
      - List of team members (emails).
      - The list can be enforced with C(enforce_members) parameter.
    type: list
  state:
    description:
      - Delete the members not found in the C(members) parameters from the
      - list of members found on the Team.
    default: present
    type: str
    choices: ["present", "absent"]
  enforce_members:
    description:
      - Delete the members not found in the C(members) parameters from the
      - list of members found on the Team.
    default: False
    type: bool
  use_proxy:
    description:
      - If C(no), it will not use a proxy, even if one is defined in an environment variable on the target hosts.
    type: bool
    default: yes
  client_cert:
    description:
      - PEM formatted certificate chain file to be used for SSL client authentication.
      - This file can also include the key as well, and if the key is included, I(client_key) is not required
    type: path
  client_key:
    description:
      - PEM formatted file that contains your private key to be used for SSL client authentication.
      - If I(client_cert) contains both the certificate and key, this option is not required.
    type: path
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated.
      - This should only set to C(no) used on personally controlled sites using self-signed certificates.
      - Prior to 1.9.2 the code defaulted to C(no).
    type: bool
    default: yes
'''

EXAMPLES = '''
---
- name: Create a team
  grafana_teams:
      url: "https://grafana.example.com"
      grafana_api_key: "{{ some_api_token_value }}"
      name: "grafana_working_group"
      email: "foo.bar@example.com"
      state: present

- name: Create a team with members
  grafana_teams:
      url: "https://grafana.example.com"
      grafana_api_key: "{{ some_api_token_value }}"
      name: "grafana_working_group"
      email: "foo.bar@example.com"
      members:
          - john.doe@example.com
          - jane.doe@example.com
      state: present

- name: Create a team with members and enforce the list of members
  grafana_teams:
      url: "https://grafana.example.com"
      grafana_api_key: "{{ some_api_token_value }}"
      name: "grafana_working_group"
      email: "foo.bar@example.com"
      members:
          - john.doe@example.com
          - jane.doe@example.com
      enforce_members: yes
      state: present

- name: Delete a team
  grafana_teams:
      url: "https://grafana.example.com"
      grafana_api_key: "{{ some_api_token_value }}"
      name: "grafana_working_group"
      email: "foo.bar@example.com"
      state: absent
'''

RETURN = '''
---
team:
    description: Information about the Team
    returned: On success
    type: complex
    contains:
        avatarUrl:
            description: The url of the Team avatar on Grafana server
            returned: always
            type: str
            sample:
                - "/avatar/a7440323a684ea47406313a33156e5e9"
        email:
            description: The Team email address
            returned: always
            type: str
            sample:
                - "foo.bar@example.com"
        id:
            description: The Team email address
            returned: always
            type: int
            sample:
                - 42
        memberCount:
            description: The number of Team members
            returned: always
            type: int
            sample:
                - 42
        name:
            description: The name of the team.
            returned: always
            type: str
            sample:
                - "grafana_working_group"
        members:
            description: The list of Team members
            returned: always
            type: list
            sample:
                - ["john.doe@exemple.com"]
        orgId:
            description: The organization id that the team is part of.
            returned: always
            type: int
            sample:
                - 1
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url, url_argument_spec, basic_auth_header

__metaclass__ = type


class GrafanaTeamInterface(object):

    def __init__(self, module):
        self._module = module
        # {{{ Authentication header
        self.headers = {"Content-Type": "application/json"}
        if module.params.get('grafana_api_key', None):
            self.headers["Authorization"] = "Bearer %s" % module.params['grafana_api_key']
        else:
            self.headers["Authorization"] = basic_auth_header(module.params['url_username'], module.params['url_password'])
        # }}}
        self.grafana_url = module.params.get("url")

    def _send_request(self, url, data=None, headers=None, method="GET"):
        if data is not None:
            data = json.dumps(data, sort_keys=True)
        if not headers:
            headers = []

        full_url = "{grafana_url}{path}".format(grafana_url=self.grafana_url, path=url)
        resp, info = fetch_url(self._module, full_url, data=data, headers=headers, method=method)
        status_code = info["status"]
        if status_code == 404:
            return None
        elif status_code == 401:
            self._module.fail_json(failed=True, msg="Unauthorized to perform action '%s' on '%s' header: %s" % (method, full_url, self.headers))
        elif status_code == 403:
            self._module.fail_json(failed=True, msg="Permission Denied")
        elif status_code == 409:
            self._module.fail_json(failed=True, msg="Team name is taken")
        elif status_code == 200:
            return self._module.from_json(resp.read())
        self._module.fail_json(failed=True, msg="Grafana Teams API answered with HTTP %d" % status_code)

    def create_team(self, name, email):
        url = "/api/teams"
        team = dict(email=email, name=name)
        response = self._send_request(url, data=team, headers=self.headers, method="POST")
        return response

    def get_team(self, name):
        url = "/api/teams/search?name={team}".format(team=name)
        response = self._send_request(url, headers=self.headers, method="GET")
        if not response.get("totalCount") <= 1:
            raise AssertionError("Expected 1 teams, got %d" % response["totalCount"])

        if len(response.get("teams")) == 0:
            return None
        return response.get("teams")[0]

    def update_team(self, team_id, name, email):
        url = "/api/teams/{team_id}".format(team_id=team_id)
        team = dict(email=email, name=name)
        response = self._send_request(url, data=team, headers=self.headers, method="PUT")
        return response

    def delete_team(self, team_id):
        url = "/api/teams/{team_id}".format(team_id=team_id)
        response = self._send_request(url, headers=self.headers, method="DELETE")
        return response

    def get_team_members(self, team_id):
        url = "/api/teams/{team_id}/members".format(team_id=team_id)
        response = self._send_request(url, headers=self.headers, method="GET")
        members = [item.get("email") for item in response]
        return members

    def add_team_member(self, team_id, email):
        url = "/api/teams/{team_id}/members".format(team_id=team_id)
        data = {"userId": self.get_user_id_from_mail(email)}
        self._send_request(url, data=data, headers=self.headers, method="POST")

    def delete_team_member(self, team_id, email):
        user_id = self.get_user_id_from_mail(email)
        url = "/api/teams/{team_id}/members/{user_id}".format(team_id=team_id, user_id=user_id)
        self._send_request(url, headers=self.headers, method="DELETE")

    def get_user_id_from_mail(self, email):
        url = "/api/users/lookup?loginOrEmail={email}".format(email=email)
        user = self._send_request(url, headers=self.headers, method="GET")
        if user is None:
            self._module.fail_json(failed=True, msg="User '%s' does not exists" % email)
        return user.get("id")


def setup_module_object():
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
        required_together=[['url_username', 'url_password']],
        mutually_exclusive=[['url_username', 'grafana_api_key']],
    )
    return module


argument_spec = url_argument_spec()
# remove unnecessary arguments
del argument_spec['force']
del argument_spec['force_basic_auth']
del argument_spec['http_agent']

argument_spec.update(
    state=dict(choices=['present', 'absent'], default='present'),
    name=dict(type='str', required=True),
    email=dict(type='str', required=True),
    members=dict(type='list', required=False),
    url=dict(type='str', required=True),
    grafana_api_key=dict(type='str', no_log=True),
    enforce_members=dict(type='bool', default=False),
    url_username=dict(aliases=['grafana_user'], default='admin'),
    url_password=dict(aliases=['grafana_password'], default='admin', no_log=True),
)


def main():

    module = setup_module_object()
    state = module.params['state']
    name = module.params['name']
    email = module.params['email']
    members = module.params['members']
    enforce_members = module.params['enforce_members']

    grafana_iface = GrafanaTeamInterface(module)

    changed = False
    if state == 'present':
        team = grafana_iface.get_team(name)
        if team is None:
            new_team = grafana_iface.create_team(name, email)
            team = grafana_iface.get_team(name)
            changed = True
        if members is not None:
            cur_members = grafana_iface.get_team_members(team.get("id"))
            plan = diff_members(members, cur_members)
            for member in plan.get("to_add"):
                grafana_iface.add_team_member(team.get("id"), member)
                changed = True
            if enforce_members:
                for member in plan.get("to_del"):
                    grafana_iface.delete_team_member(team.get("id"), member)
                    changed = True
            team = grafana_iface.get_team(name)
        team['members'] = grafana_iface.get_team_members(team.get("id"))
        module.exit_json(failed=False, changed=changed, team=team)
    elif state == 'absent':
        team = grafana_iface.get_team(name)
        if team is None:
            module.exit_json(failed=False, changed=False, message="No team found")
        result = grafana_iface.delete_team(team.get("id"))
        module.exit_json(failed=False, changed=True, message=result.get("message"))


def diff_members(target, current):
    diff = {"to_del": [], "to_add": []}
    for member in target:
        if member not in current:
            diff["to_add"].append(member)
    for member in current:
        if member not in target:
            diff["to_del"].append(member)
    return diff


if __name__ == '__main__':
    main()
