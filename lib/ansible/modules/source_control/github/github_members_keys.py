#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Sebastián Estrella <sestrella.me@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: github_members_keys

short_description: Fetches GitHub team members SSH keys

description:
    - Fetches GitHub team members SSH keys

version_added: '2.10'

author:
    - Sebastián Estrella (@sestrella)

options:
    token:
        description:
            - GitHub API access token
        type: str
        required: true
    organization:
        description:
            - GitHub organization name
        type: str
        required: true
    team:
        description:
            - GitHub team name
        type: str
        required: true
    mandatory_members:
        description:
            - List of members that must be part of the team
            - If a member is not part of the team it raises an error
            - If a member has no keys it raises an error
            - Each member corresponds to a GitHub username
            - Check used to avoid locking members out of a server
        type: list
        required: false
        default: []

requirements:
    - PyGithub
'''

EXAMPLES = '''
- name: Fetch team members SSH keys
  local_action:
    module: github_members_keys
    token: token
    organization: organization
    team: team
    mandatory_members:
      - admin
  register: result

- name: Set authorized_key taken from GitHub
  authorized_key:
    user: user
    key: "{{ result.members_keys | join('\n') }}"
    exclusive: yes
'''

RETURN = '''
members_keys:
    description: A list of team members keys
    type: list
    returned: success
    sample: ["ssh-rsa AAA... user1-1", "ssh-rsa BBB... user1-2"]
'''

import traceback

GITHUB_IMP_ERR = None
try:
    import github
    HAS_GITHUB = True
except ImportError:
    HAS_GITHUB = False
    GITHUB_IMP_ERR = traceback.format_exc()

import json

from ansible.module_utils.basic import AnsibleModule, missing_required_lib


class GithubClient:
    def __init__(self, token):
        self.client = github.Github(token)

    def get_organization_team(self, organization, team):
        organization = self.client.get_organization(organization)
        return OrganizationTeam(organization.get_team_by_slug(team))


class OrganizationTeam:
    def __init__(self, team):
        self.team = team

    def get_members_keys(self):
        return MembersKeys(self.team.get_members())


class MembersKeys(object):
    def __init__(self, members):
        self.members = iter(members)

    def __iter__(self):
        return self

    def __next__(self):
        member = next(self.members)
        return MemberKeys(member, member.get_keys())

    def next(self):
        return self.__next__()


class MemberKeys:
    def __init__(self, member, keys):
        self.member = member
        self.keys = keys

    @property
    def login(self):
        return self.member.login

    def is_mandatory_without_keys(self, mandatory_members):
        not_have_keys = len(list(self.keys)) == 0
        return self.login in mandatory_members and not_have_keys


def main():
    argument_spec = dict(
        token=dict(type='str', required=True, no_log=True),
        organization=dict(type='str', required=True),
        team=dict(type='str', required=True),
        mandatory_members=dict(type='list', required=False, default=[])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_GITHUB:
        module.fail_json(
            msg=missing_required_lib('PyGithub'),
            exception=GITHUB_IMP_ERR
        )

    client = GithubClient(module.params['token'])
    team = client.get_organization_team(
        module.params['organization'],
        module.params['team']
    )

    mandatory_members = module.params['mandatory_members']
    included_members = []
    members_keys = []

    for member_keys in team.get_members_keys():
        login = member_keys.login
        included_members.append(login)

        if member_keys.is_mandatory_without_keys(mandatory_members):
            module.fail_json(msg='Mandatory member %s has no keys' % login)

        for key in member_keys.keys:
            members_keys.append('%s %s-%s' % (key.key, login, key.id))

    if mandatory_members:
        missing_members = [
            member for member in mandatory_members
            if member not in included_members
        ]

        if missing_members:
            module.fail_json(msg='%s does not include all mandatory members %s' % (
                included_members,
                missing_members
            ))

    module.exit_json(changed=False, members_keys=members_keys)


if __name__ == '__main__':
    main()
