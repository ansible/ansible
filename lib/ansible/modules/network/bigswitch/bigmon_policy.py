#!/usr/bin/python
# -*- coding: utf-8 -*-

# Ansible module to manage Big Monitoring Fabric service chains
# (c) 2016, Ted Elhourani <ted@bigswitch.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: bigmon_policy
author: "Ted (@tedelhourani)"
short_description: Create and remove a bigmon out-of-band policy.
description:
    - Create and remove a bigmon out-of-band policy.
version_added: "2.3"
options:
  name:
    description:
     - The name of the policy.
    required: true
  policy_description:
    description:
     - Description of policy.
  action:
    description:
     - Forward matching packets to delivery interfaces, Drop is for measure rate of matching packets,
       but do not forward to delivery interfaces, capture packets and write to a PCAP file, or enable NetFlow generation.
    default: forward
    choices: ['forward', 'drop', 'flow-gen']
  priority:
    description:
     - A priority associated with this policy. The higher priority policy takes precedence over a lower priority.
    default: 100
  duration:
    description:
     - Run policy for duration duration or until delivery_packet_count packets are delivered, whichever comes first.
    default: 0
  start_time:
    description:
     - Date the policy becomes active
    default: ansible_date_time.iso8601
  delivery_packet_count:
    description:
     - Run policy until delivery_packet_count packets are delivered.
    default: 0
  state:
    description:
     - Whether the policy should be present or absent.
    default: present
    choices: ['present', 'absent']
  controller:
    description:
     - The controller address.
    required: true
  validate_certs:
    description:
     - If C(false), SSL certificates will not be validated. This should only be used
       on personally controlled devices using self-signed certificates.
    required: false
    default: true
    choices: [true, false]
  access_token:
    description:
     - Bigmon access token. If this isn't set, the environment variable C(BIGSWITCH_ACCESS_TOKEN) is used.

'''

EXAMPLES = '''
- name: policy to aggregate filter and deliver data center (DC) 1 traffic
  bigmon_policy:
    name: policy1
    policy_description: DC 1 traffic policy
    action: drop
    controller: '{{ inventory_hostname }}'
    state: present
    validate_certs: false
'''

RETURN = ''' # '''

import datetime
import os
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.bigswitch.bigswitch import Rest
from ansible.module_utils._text import to_native


def policy(module):
    try:
        access_token = module.params['access_token'] or os.environ['BIGSWITCH_ACCESS_TOKEN']
    except KeyError as e:
        module.fail_json(msg='Unable to load %s' % e.message, exception=traceback.format_exc())

    name = module.params['name']
    policy_description = module.params['policy_description']
    action = module.params['action']
    priority = module.params['priority']
    duration = module.params['duration']
    start_time = module.params['start_time']
    delivery_packet_count = module.params['delivery_packet_count']
    state = module.params['state']
    controller = module.params['controller']

    rest = Rest(module,
                {'content-type': 'application/json', 'Cookie': 'session_cookie=' + access_token},
                'https://' + controller + ':8443/api/v1/data/controller/applications/bigtap')

    if name is None:
        module.fail_json(msg='parameter `name` is missing')

    response = rest.get('policy?config=true', data={})
    if response.status_code != 200:
        module.fail_json(msg="failed to obtain existing policy config: {}".format(response.json['description']))

    config_present = False

    matching = [policy for policy in response.json
                if policy['name'] == name and
                policy['duration'] == duration and
                policy['delivery-packet-count'] == delivery_packet_count and
                policy['policy-description'] == policy_description and
                policy['action'] == action and
                policy['priority'] == priority]

    if matching:
        config_present = True

    if state in ('present') and config_present:
        module.exit_json(changed=False)

    if state in ('absent') and not config_present:
        module.exit_json(changed=False)

    if state in ('present'):
        data = {'name': name, 'action': action, 'policy-description': policy_description,
                'priority': priority, 'duration': duration, 'start-time': start_time,
                'delivery-packet-count': delivery_packet_count}

        response = rest.put('policy[name="%s"]' % name, data=data)
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error creating policy '{}': {}".format(name, response.json['description']))

    if state in ('absent'):
        response = rest.delete('policy[name="%s"]' % name, data={})
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.fail_json(msg="error deleting policy '{}': {}".format(name, response.json['description']))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            policy_description=dict(type='str', default=''),
            action=dict(choices=['forward', 'drop', 'capture', 'flow-gen'], default='forward'),
            priority=dict(type='int', default=100),
            duration=dict(type='int', default=0),
            start_time=dict(type='str', default=datetime.datetime.now().isoformat() + '+00:00'),
            delivery_packet_count=dict(type='int', default=0),
            controller=dict(type='str', required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            validate_certs=dict(type='bool', default='True'),
            access_token=dict(type='str', no_log=True)
        )
    )

    try:
        policy(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=traceback.format_exc())

if __name__ == '__main__':
    main()
