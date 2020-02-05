#!/usr/bin/python
#
# Scaleway Security Group Rule management module
#
# Copyright (C) 2018 Antoine Barbare (antoinebarbare@gmail.com).
#
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: scaleway_security_group_rule
short_description: Scaleway Security Group Rule management module
version_added: "2.8"
author: Antoine Barbare (@abarbare)
description:
    - This module manages Security Group Rule on Scaleway account
      U(https://developer.scaleway.com)
extends_documentation_fragment: scaleway

options:
  state:
    description:
      - Indicate desired state of the Security Group Rule.
    default: present
    choices:
      - present
      - absent

  region:
    description:
      - Scaleway region to use (for example C(par1)).
    required: true
    choices:
      - ams1
      - EMEA-NL-EVS
      - par1
      - EMEA-FR-PAR1

  protocol:
    description:
      - Network protocol to use
    choices:
      - TCP
      - UDP
      - ICMP
    required: true

  port:
    description:
      - Port related to the rule, null value for all the ports
    required: true
    type: int

  ip_range:
    description:
      - IPV4 CIDR notation to apply to the rule
    default: 0.0.0.0/0

  direction:
    description:
      - Rule direction
    choices:
      - inbound
      - outbound
    required: true

  action:
    description:
      - Rule action
    choices:
      - accept
      - drop
    required: true

  security_group:
    description:
      - Security Group unique identifier
    required: true
'''

EXAMPLES = '''
  - name: Create a Security Group Rule
    scaleway_security_group_rule:
      state: present
      region: par1
      protocol: TCP
      port: 80
      ip_range: 0.0.0.0/0
      direction: inbound
      action: accept
      security_group: b57210ee-1281-4820-a6db-329f78596ecb
    register: security_group_rule_creation_task
'''

RETURN = '''
data:
    description: This is only present when C(state=present)
    returned: when C(state=present)
    type: dict
    sample: {
        "scaleway_security_group_rule": {
            "direction": "inbound",
            "protocol": "TCP",
            "ip_range": "0.0.0.0/0",
            "dest_port_from": 80,
            "action": "accept",
            "position": 2,
            "dest_port_to": null,
            "editable": null,
            "id": "10cb0b9a-80f6-4830-abd7-a31cd828b5e9"
        }
    }
'''

from ansible.module_utils.scaleway import SCALEWAY_LOCATION, scaleway_argument_spec, Scaleway, payload_from_object
from ansible.module_utils.compat.ipaddress import ip_network
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule


def get_sgr_from_api(security_group_rules, security_group_rule):
    """ Check if a security_group_rule specs are present in security_group_rules
        Return None if no rules match the specs
        Return the rule if found
    """
    for sgr in security_group_rules:
        if (sgr['ip_range'] == security_group_rule['ip_range'] and sgr['dest_port_from'] == security_group_rule['dest_port_from'] and
            sgr['direction'] == security_group_rule['direction'] and sgr['action'] == security_group_rule['action'] and
                sgr['protocol'] == security_group_rule['protocol']):
            return sgr

    return None


def present_strategy(api, security_group_id, security_group_rule):
    ret = {'changed': False}

    response = api.get('security_groups/%s/rules' % security_group_id)
    if not response.ok:
        api.module.fail_json(
            msg='Error getting security group rules "%s": "%s" (%s)' %
            (response.info['msg'], response.json['message'], response.json))

    existing_rule = get_sgr_from_api(
        response.json['rules'], security_group_rule)

    if not existing_rule:
        ret['changed'] = True
        if api.module.check_mode:
            return ret

        # Create Security Group Rule
        response = api.post('/security_groups/%s/rules' % security_group_id,
                            data=payload_from_object(security_group_rule))

        if not response.ok:
            api.module.fail_json(
                msg='Error during security group rule creation: "%s": "%s" (%s)' %
                (response.info['msg'], response.json['message'], response.json))
        ret['scaleway_security_group_rule'] = response.json['rule']

    else:
        ret['scaleway_security_group_rule'] = existing_rule

    return ret


def absent_strategy(api, security_group_id, security_group_rule):
    ret = {'changed': False}

    response = api.get('security_groups/%s/rules' % security_group_id)
    if not response.ok:
        api.module.fail_json(
            msg='Error getting security group rules "%s": "%s" (%s)' %
            (response.info['msg'], response.json['message'], response.json))

    existing_rule = get_sgr_from_api(
        response.json['rules'], security_group_rule)

    if not existing_rule:
        return ret

    ret['changed'] = True
    if api.module.check_mode:
        return ret

    response = api.delete(
        '/security_groups/%s/rules/%s' %
        (security_group_id, existing_rule['id']))
    if not response.ok:
        api.module.fail_json(
            msg='Error deleting security group rule "%s": "%s" (%s)' %
            (response.info['msg'], response.json['message'], response.json))

    return ret


def core(module):
    api = Scaleway(module=module)

    security_group_rule = {
        'protocol': module.params['protocol'],
        'dest_port_from': module.params['port'],
        'ip_range': module.params['ip_range'],
        'direction': module.params['direction'],
        'action': module.params['action'],
    }

    region = module.params['region']
    module.params['api_url'] = SCALEWAY_LOCATION[region]['api_endpoint']

    if module.params['state'] == 'present':
        summary = present_strategy(
            api=api,
            security_group_id=module.params['security_group'],
            security_group_rule=security_group_rule)
    else:
        summary = absent_strategy(
            api=api,
            security_group_id=module.params['security_group'],
            security_group_rule=security_group_rule)
    module.exit_json(**summary)


def main():
    argument_spec = scaleway_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        region=dict(type='str', required=True, choices=SCALEWAY_LOCATION.keys()),
        protocol=dict(type='str', required=True, choices=['TCP', 'UDP', 'ICMP']),
        port=dict(type='int', required=True),
        ip_range=dict(type='str', default='0.0.0.0/0'),
        direction=dict(type='str', required=True, choices=['inbound', 'outbound']),
        action=dict(type='str', required=True, choices=['accept', 'drop']),
        security_group=dict(type='str', required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    core(module)


if __name__ == '__main__':
    main()
