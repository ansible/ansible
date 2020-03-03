#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: elb_security_group
short_description: Attach a security group to an already existing elb
description:
  - Attach a security group to an elb
requirements: ['boto3 >= 1.11.15']
version_added: "2.10"
author:
  - "Michael Moyle (@mmoyle)"
options:
    alb_arn:
        description: ARN of an existing application load balancer
        type: str
        required: true
    security_group_ids:
        description: List of security groups IDs to attach to alb
        type: list
        elements: str
        required: true
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: Attach SGs to alb
  elb_security_group:
    profile: 'my_aws_profile'
    region: 'my_region'
    alb_arn: "arn:aws:elasticloadbalancing:..."
    security_group_ids: ['sg-1aaaa', 'sg-2bbbb']
  register: alb_sg
- debug:
    msg: "{{ alb_sg }}"
'''

RETURN = '''
response:
    description: The number or security groups attached.
    returned: Always
    type: int
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import AWSRetry

try:
    from botocore.exceptions import ClientError
    from botocore.exceptions import BotoCoreError
except ImportError:
    pass  # handled by AnsibleAWSModule


@AWSRetry.exponential_backoff()
def elb_sg_attach(elbv2_client, alb_arn, sg_ids):
    '''Attach security groups to elb and return number of sgs attached '''

    response = elbv2_client.set_security_groups(
        LoadBalancerArn=alb_arn,
        SecurityGroups=sg_ids
    )

    return len(response['SecurityGroupIds'])


def main():
    argument_spec = dict(
        alb_arn=dict(required=True, type='str'),
        security_group_ids=dict(required=True, type='list', elements='str')
    )
    result = dict(
        changed=False,
        original_message=''
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=False)
    elbv2_client = module.client('elbv2')

    try:
        result['response'] = elb_sg_attach(
            elbv2_client,
            module.params.get('alb_arn'),
            module.params.get('security_group_ids')
        )

        result['changed'] = True

    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e)

    result.update()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
