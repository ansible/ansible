#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: aws_waf_associate_elbv2
short_description: Associate/disassociate WAF Regional rules with ELBv2 (ALB).
description:
  - Associate/disassociate WAF Regional rules with ELBv2 (ALB).
version_added: "2.6"
requirements: [ boto3 ]
options:
  web_acl_id:
    description:
      - Web ACL ID
  alb_resource_arn:
    description:
      - ALB resource ARN

author:
  - Jaco Engelbrecht (@bje)
  - Mike Mochan (@mmochan)
extends_documentation_fragment:
    - aws
    - elb_application_lb
'''

EXAMPLES = '''
- elb_application_lb_facts:
    names:
      - alb-test-webapp
  register: alb_arn

- aws_waf_regional_facts:
    name: Drop HTTP requests for abusive API keys
  register: waf_web_acl_id

- name: Associate WAF Regional Web ACL with an ELBv2 (ALB)
  aws_waf_regional_associate_elbv2:
    web_acl_id: "{{ waf_web_acl_id.wafs[0].web_acl_id }}"
    alb_resource_arn: "{{ alb_arn.load_balancers[0].load_balancer_arn }}"
    state: present

- name: Disassociate WAF Regional Web ACL with an ELBv2 (ALB)
  aws_waf_regional_associate_elbv2:
    web_acl_id: "{{ waf_web_acl_id.wafs[0].web_acl_id }}"
    alb_resource_arn: "{{ alb_arn.load_balancers[0].load_balancer_arn }}"
    state: absent
'''

RETURN = '''
changed:
    description: True if change succeeded succesfully.
    type: bool
    returned: always
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, AWSRetry, compare_policies
from ansible.module_utils.aws.waf_regional import run_func_with_change_token_backoff, MATCH_LOOKUP
from ansible.module_utils.aws.waf_regional import get_rule_with_backoff, list_rules_with_backoff

def main():
    filters_subspec = dict(
        web_acl_id=dict(),
        alb_resource_arn=dict(),
    )
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            web_acl_id=dict(required=True),
            alb_resource_arn=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
        ),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['state', 'present', ['web_acl_id','alb_resource_arn']]])
    state = module.params.get('state')
    web_acl_id = module.params.get('web_acl_id')
    alb_resource_arn = module.params.get('alb_resource_arn')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='waf-regional', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    results = dict(changed=False)

    if state == 'present':
        response = client.associate_web_acl(
            WebACLId=web_acl_id,
            ResourceArn=alb_resource_arn
        )
        results['changed'] = True
    else:
        response = client.disassociate_web_acl(
            ResourceArn=alb_resource_arn
        )
        results['changed'] = True

    pretty_results = camel_dict_to_snake_dict(results)
    module.exit_json(**pretty_results)

if __name__ == '__main__':
    main()
