#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: aws_guardduty_detector
short_description: Enable/Disable the AWS GuardDuty detector.
description:
    - Enable/Disable the GuardDuty detector for a given AWS account.
author: "Aaron Smith (@slapula)"
version_added: "2.7"
requirements: [ 'botocore', 'boto3' ]
options:
  state:
    description:
     - Whether the detector should be exist or not.
    required: true
    choices: ['present', 'absent']
  enabled:
    description:
     - Whether the detector should be enabled or disabled.
    type: bool
    default: true
extends_documentation_fragment:
    - ec2
    - aws
notes:
  - Currently, GuardDuty supports only one detector resource per AWS account per region.
'''


EXAMPLES = r'''
- name: create GuardDuty detector
  guardduty_detector:
    state: present
    enabled: true

- name: disable GuardDuty detector
  guardduty_detector:
    state: present
    enabled: false

- name: delete GuardDuty detector
  guardduty_detector:
    state: absent
'''


RETURN = r'''
detector_id:
    description: The ID of the GuardDuty detector you just created or updated.
    returned: always
    type: string
'''

import os

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def detector_exists(client, module, result):
    try:
        response = client.list_detectors()
        return {'exists': True, 'detector_id': response['DetectorIds'][0]}
    except (ClientError, IndexError):
        return {'exists': False}

    return {'exists': False}


def create_detector(client, module):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_detector(
            Enable=module.params.get('enabled')
        )
        return {'changed': True, 'detector_id': response['DetectorId']}
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to enable detector")


def update_detector(client, module, status):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.update_detector(
            DetectorId=status['detector_id'],
            Enable=module.params.get('enabled')
        )
        return {'changed': True, 'detector_id': status['detector_id']}
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update detector")


def delete_detector(client, module, status):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_detector(
            DetectorId=status['detector_id']
        )
        return {'changed': True, 'detector_id': status['detector_id']}
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete detector")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'state': dict(type='str', choices=['present', 'absent'], required=True),
            'enabled': dict(type='bool', default=True),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False,
        'detector_id': ''
    }

    desired_state = module.params.get('state')

    client = module.client('guardduty')

    detector_status = detector_exists(client, module, result)

    if desired_state == 'present':
        if not detector_status['exists']:
            result = create_detector(client, module)
        if detector_status['exists']:
            result = update_detector(client, module, detector_status)

    if desired_state == 'absent':
        if detector_status['exists']:
            result = delete_detector(client, module, detector_status)

    module.exit_json(changed=result['changed'], detector_id=result['detector_id'])


if __name__ == '__main__':
    main()
