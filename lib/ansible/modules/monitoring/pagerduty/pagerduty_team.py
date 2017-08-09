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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'supported_by': 'community',
    'status': 'preview'
}

DOCUMENTATION = '''
module: pagerduty_team
short_description: Manage PagerDuty team creation and deletion
description:
    - This module will let you manage PagerDuty teams. Available actions are creation, deletion, and updating. Managing users and team membership is not provided.
version_added: "2.3"
author: "Matty Jones (@mattyjones)"
requirements:
    - PagerDuty API access
options:
    desc:
        description:
            - A description of the team
        required: False
        default:  Managed by Ansible
        choices:  []
        aliases:  []
        type:     string
    name:
        description:
            - The name of the Pagerduty team.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    password:
        description:
            - PagerDuty user password.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    requester_id:
        description:
            - Email of user making the request.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    state:
        description:
            - Create or destroy a team.
        required: True
        default:  null
        choices:  [ absent", "present" ]
        aliases:  []
        type:     string
    token:
        description:
            - A pagerduty token, generated on the pagerduty site. Should be used instead of
              user/password combination.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
    user_name:
        description:
            - PagerDuty user ID.
        required: True
        default:  null
        choices:  []
        aliases:  []
        type:     string
'''

EXAMPLES = '''
- name: Create a new team with a username and password
  pagerduty_team:
    name:        ops
    user_name:   john@example.com
    password:    password123
    state:       present
    desc:        'traditional operations team'

- name: Create a new team with a token
  pagerduty_team:
    name:  engineering
    token: xxxxxxxxxxxxxx
    state: present
    desc:  'traditional engineering team'

- name: Update a team
  pagerduty_team:
    name:  engineering
    token: xxxxxxxxxxxxxx
    state: present
    desc:  'this team makes life hard'

- name: Delete a team
  pagerduty_team:
    name:  engineering
    token: xxxxxxxxxxxxxx
    state: absent
'''

RETURN = '''
name:
    description: team name
    returned: changed
    type: string
    sample: engineering
id:
    description: the Pagerduty id
    returned: success
    type: string
    sample: PNQ57GY
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pagerduty_common import *

try:
    import json
except ImportError:
    import simplejson as json


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            desc=dict(default='Managed by Ansible',
                      required=False, type='str'),
            name=dict(required=False, default='no-op', type='str'),
            token=dict(required=False, type='str'),
            user_name=dict(required=False, type='str'),
            password=dict(required=False, type='str'),
            requester_id=dict(required=True, type='str'),
            generate_list=dict(required=False, type='bool'),
            remote_data=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    acc_state = module.params['state']
    obj_type = 'teams'
    team_name = module.params['name']

    if module.params['generate_list']:
        remote_d = fetchRemoteData(obj_type, module)
        with open(module.params['remote_data'], 'w') as f:
            f.write(json.dumps(remote_d))
        module.exit_json(msg="Dumped current pagerduty state to a file")

    # Get a json blob of remote data
    if not module.params['remote_data']:
        remote_d = fetchRemoteData(obj_type, module)
    else:
        with open(module.params['remote_data']) as json_file:
            remote_d = json.load(json_file)

    # Create the master list of remote objects for easy parsing
    remote_master = createObjectList(obj_type, remote_d)

    # If we don't want the team
    if acc_state == 'absent' and team_name in remote_master:
        deleteObj(obj_type, remote_d, module)
        module.exit_json(changed=True, msg="we deleted the team: %s" %
                         (module.params['name']))
    if acc_state == 'absent' and team_name not in remote_master:
        module.exit_json(changed=False, msg="the team %s was not present" %
                         (module.params['name']))

    # If we do want the team
    if acc_state == 'present' and team_name not in remote_master:
        createObj(obj_type, module)
        module.exit_json(changed=True, msg="we added the team: %s" %
                         (module.params['name']))
    elif acc_state == 'present' and team_name in remote_master:
        update = checkUpdateObj(obj_type, module, remote_d)
        if update:
            module.exit_json(changed=True, msg="we updated the team: %s" %
                             (module.params['name']))
        else:
            module.exit_json(changed=False, msg="no updates detected for team: %s" %
                             (module.params['name']))


if __name__ == '__main__':
    main()
