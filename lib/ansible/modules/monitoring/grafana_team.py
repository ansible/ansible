
# Copyright: (c) 2019, Manuel Bovo <manuel.bovo@gmail.com>
# MIT License (see LICENSE.md )

from __future__ import absolute_import, division, print_function

from ansible.module_utils.api import basic_auth_argument_spec
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_text, to_native
from urllib.parse import urlparse
import json
import traceback

GITLAB_IMP_ERR = None
try:
    from grafana_api.grafana_face import GrafanaFace
    HAS_GRAFANA_PACKAGE = True
except Exception:
    GRAFANA_IMP_ERR = traceback.format_exc()
    HAS_GRAFANA_PACKAGE = False

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: grafana_team
author:
  - Manuel Bovo (@mbovo)
version_added: 2.9
short_description: Manage Grafana Teams
description:
    - "Create, update, delete Grafana Teams"
options:
    
'''

EXAMPLES = '''
- hosts: localhost
  connection: local
  tasks:
    - name: Create Team
      grafana_team:
        state: present
        grafana_url: "https://grafana.com"
        grafana_user: "admin"
        grafana_password: "admin"
        validate_certs: false
        name: "teamName"
        email: "team@email.com"
'''

RETURN = '''
members:
    description: The list of tuples (id, login, email)
    type: list
    returned: onSuccess
teamId:
    description: the team ID
    type: str
    returned: onSuccess
'''

__metaclass__ = type


def grafana_search_team(graf: GrafanaFace, teamName: str):
  exists = False
  teamId = None
  members = None

  teamList = graf.teams.search_teams(teamName)
  if len(teamList) > 0:
    exists = True
    teamId = teamList[0]['id']
    members = graf.teams.get_team_members(teamId)

  return (exists, teamId, members)


def grafana_update_members(graf: GrafanaFace, module: AnsibleModule, data: dict, teamID: int):
  addedUsers = []
  if data['members'] is not None:
    for member in data['members']:
      userList = graf.users.find_user(member)
      if userList is None or len(userList) == 0:
        raise GrafanaAPIException("Cannot find id for user %s" % member)
      for user in userList:
        addedUsers.append((user['userId'], user['login'], user['email']))

  for (userId, login, email) in addedUsers:
    graf.teams.add_team_member(teamID, userId)

  return addedUsers


def grafana_create_team(graf: GrafanaFace, module: AnsibleModule, data):
  team_exists, teamID, members = grafana_search_team(graf, data['name'])
  if team_exists:
    graf.teams.update_team(teamID, {
        "name": data['name'],
        "email": data['email']
    })
  else:
    resp = graf.teams.add_team({
        "name": data['name'],
        "email": data['email']
    })
    if 'teamId' not in resp:
      raise GrafanaAPIException('Invalid ID retrieved when creating a Team')
    teamID = resp['teamId']

  addedUsers = grafana_update_members(graf, AnsibleModule, data, teamID)

  return {'teamId': teamID, 'members': addedUsers}


def grafana_delete_team(graf: GrafanaFace, moudle: AnsibleModule, data):
  team_exists, teamId, members = grafana_search_team(graf, data['name'])
  if team_exists:
    ret = graf.teams.delete_team(teamId)
  else:
    ret = "Not found"

  return {"result": ret['message']}


class GrafanaAPIException(Exception):
  pass


def main():
  argument_spec = basic_auth_argument_spec()
  argument_spec.update(
      state=dict(choices=['present', 'absent'], default='present'),
      api_url=dict(aliases=['url', 'grafana_url'], type='str', required=True),
      api_username=dict(aliases=['grafana_user'], type='str', default='admin'),
      api_password=dict(aliases=['grafana_password'],
                        type='str', default='admin', no_log=True),
      grafana_api_key=dict(aliases=['api_key'], type='str', no_log=True),
      # validate_certs inherited from basib_auth_argument_spec
      name=dict(type='str', required=True, aliases=['team_name']),
      email=dict(type='str', required=True, aliases=['team_email', 'mailbox']),
      members=dict(type='list', defalt=[])
  )

  module = AnsibleModule(
      argument_spec=argument_spec,
      supports_check_mode=False,
      required_together=[['api_username', 'api_password']],
      mutually_exclusive=[['grafana_api_key', 'api_username'], [
          'grafana_api_key', 'api_password']],
      required_one_of=[['grafana_api_key', 'api_username']]
  )

  if not HAS_GRAFANA_PACKAGE:
        module.fail_json(msg=missing_required_lib(
            "grafana-api"), exception=GRAFANA_IMP_ERR)

  try:

    if module.params['grafana_api_key'] is not None:
      auth = module.params['grafana_api_key']
    else:
      auth = (module.params['api_username'], module.params['api_password'])

    uri = urlparse(module.params['api_url'])

    graf = GrafanaFace(auth,
                       host=uri.hostname,
                       port=uri.port,
                       protocol=uri.scheme,
                       verify=module.params['validate_certs']
                       )

    if module.params['state'] == 'present':
      result = grafana_create_team(graf, module, module.params)
    else:
      result = grafana_delete_team(graf, module, module.params)
  except Exception as e:
    module.fail_json(
        failed=True,
        msg="error: %s" % to_native(e)
    )

    return

  module.exit_json(
      failed=False,
      **result
  )
  return


if __name__ == '__main__':
    main()
