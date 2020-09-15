#!/usr/bin/python
#
# Scaleway Security Group management module
#
# Copyright (C) 2018 Antoine Barbare (antoinebarbare@gmail.com).
#
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
module: scaleway_security_group
short_description: Scaleway Security Group management module
version_added: "2.8"
author: Antoine Barbare (@abarbare)
description:
    - This module manages Security Group on Scaleway account
      U(https://developer.scaleway.com).
extends_documentation_fragment: scaleway

options:
  state:
    description:
      - Indicate desired state of the Security Group.
    type: str
    choices: [ absent, present ]
    default: present

  organization:
    description:
      - Organization identifier.
    type: str
    required: true

  region:
    description:
      - Scaleway region to use (for example C(par1)).
    type: str
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1

  name:
    description:
      - Name of the Security Group.
    type: str
    required: true

  description:
    description:
      - Description of the Security Group.
    type: str

  stateful:
    description:
      - Create a stateful security group which allows established connections in and out.
    type: bool
    required: true

  inbound_default_policy:
    description:
      - Default policy for incoming traffic.
    type: str
    choices: [ accept, drop ]

  outbound_default_policy:
    description:
      - Default policy for outcoming traffic.
    type: str
    choices: [ accept, drop ]

  organization_default:
    description:
      - Create security group to be the default one.
    type: bool
'''

EXAMPLES = '''
  - name: Create a Security Group
    scaleway_security_group:
      state: present
      region: par1
      name: security_group
      description: "my security group description"
      organization: "43a3b6c8-916f-477b-b7ec-ff1898f5fdd9"
      stateful: false
      inbound_default_policy: accept
      outbound_default_policy: accept
      organization_default: false
    register: security_group_creation_task
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_security_group": {
            "description": "my security group description",
            "enable_default_security": true,
            "id": "0168fb1f-cc46-4f69-b4be-c95d2a19bcae",
            "inbound_default_policy": "accept",
            "name": "security_group",
            "organization": "43a3b6c8-916f-477b-b7ec-ff1898f5fdd9",
            "organization_default": false,
            "outbound_default_policy": "accept",
            "servers": [],
            "stateful": false
        }
    }
'''

from ansible.module_utils.scaleway import SCALEWAY_LOCATION, scaleway_argument_spec, Scaleway
from ansible.module_utils.basic import AnsibleModule
from uuid import uuid4


def payload_from_security_group(security_group):
    return dict(
        (k, v)
        for k, v in security_group.items()
        if k != 'id' and v is not None
    )


def present_strategy(api, security_group):
    ret = {'changed': False}

    response = api.get('security_groups')
    if not response.ok:
        api.module.fail_json(msg='Error getting security groups "%s": "%s" (%s)' % (response.info['msg'], response.json['message'], response.json))

    security_group_lookup = dict((sg['name'], sg)
                                 for sg in response.json['security_groups'])

    if security_group['name'] not in security_group_lookup.keys():
        ret['changed'] = True
        if api.module.check_mode:
            # Help user when check mode is enabled by defining id key
            ret['scaleway_security_group'] = {'id': str(uuid4())}
            return ret

        # Create Security Group
        response = api.post('/security_groups',
                            data=payload_from_security_group(security_group))

        if not response.ok:
            msg = 'Error during security group creation: "%s": "%s" (%s)' % (response.info['msg'], response.json['message'], response.json)
            api.module.fail_json(msg=msg)
        ret['scaleway_security_group'] = response.json['security_group']

    else:
        ret['scaleway_security_group'] = security_group_lookup[security_group['name']]

    return ret


def absent_strategy(api, security_group):
    response = api.get('security_groups')
    ret = {'changed': False}

    if not response.ok:
        api.module.fail_json(msg='Error getting security groups "%s": "%s" (%s)' % (response.info['msg'], response.json['message'], response.json))

    security_group_lookup = dict((sg['name'], sg)
                                 for sg in response.json['security_groups'])
    if security_group['name'] not in security_group_lookup.keys():
        return ret

    ret['changed'] = True
    if api.module.check_mode:
        return ret

    response = api.delete('/security_groups/' + security_group_lookup[security_group['name']]['id'])
    if not response.ok:
        api.module.fail_json(msg='Error deleting security group "%s": "%s" (%s)' % (response.info['msg'], response.json['message'], response.json))

    return ret


def core(module):
    security_group = {
        'organization': module.params['organization'],
        'name': module.params['name'],
        'description': module.params['description'],
        'stateful': module.params['stateful'],
        'inbound_default_policy': module.params['inbound_default_policy'],
        'outbound_default_policy': module.params['outbound_default_policy'],
        'organization_default': module.params['organization_default'],
    }

    region = module.params['region']
    module.params['api_url'] = SCALEWAY_LOCATION[region]['api_endpoint']

    api = Scaleway(module=module)
    if module.params['state'] == 'present':
        summary = present_strategy(api=api, security_group=security_group)
    else:
        summary = absent_strategy(api=api, security_group=security_group)
    module.exit_json(**summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        organization=dict(type='str', required=True),
        name=dict(type='str', required=True),
        description=dict(type='str'),
        region=dict(type='str', required=True, choices=SCALEWAY_LOCATION.keys()),
        stateful=dict(type='bool', required=True),
        inbound_default_policy=dict(type='str', choices=['accept', 'drop']),
        outbound_default_policy=dict(type='str', choices=['accept', 'drop']),
        organization_default=dict(type='bool'),
    ))
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['stateful', True, ['inbound_default_policy', 'outbound_default_policy']]]
    )

    core(module)


if __name__ == '__main__':
    main()
