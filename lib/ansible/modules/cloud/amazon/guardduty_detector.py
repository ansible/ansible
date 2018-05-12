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
module: guardduty_detector
short_description: Enable/Disable the AWS GuardDuty detector.
description:
    - Enable/Disable the GuardDuty detector for a given AWS account.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
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


RETURN = r'''#'''

import os

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def detector_exists(client, module, result):
    try:
        response = client.list_detectors()
        result['detector_id'] = response['DetectorIds'][0]
        return True
    except (ClientError, IndexError):
        return False

    return False


def create_detector(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_detector(
            Enable=module.params.get('enabled')
        )
        result['detector_id'] = response['DetectorId']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to enable detector")


def update_detector(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.update_detector(
            DetectorId=result['detector_id'],
            Enable=module.params.get('enabled')
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update detector")


def delete_detector(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_detector(
            DetectorId=result['detector_id']
        )
        result['changed'] = True
        return result
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
        'changed': False
    }

    desired_state = module.params.get('state')

    client = module.client('guardduty')

    detector_status = detector_exists(client, module, result)

    if desired_state == 'present':
        if not detector_status:
            create_detector(client, module, result)
        if detector_status:
            update_detector(client, module, result)

    if desired_state == 'absent':
        if detector_status:
            delete_detector(client, module, result)

    module.exit_json(changed=result['changed'], results=result)


if __name__ == '__main__':
    main()
