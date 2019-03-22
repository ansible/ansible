#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: aws_waf_facts
short_description: Retrieve facts for WAF ACLs, Rule , Conditions and Filters.
description:
  - Retrieve facts for WAF ACLs, Rule , Conditions and Filters.
version_added: "2.4"
requirements: [ boto3 ]
options:
  name:
    description:
      - The name of a Web Application Firewall

author:
  - Mike Mochan (@mmochan)
  - Will Thames (@willthames)
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: obtain all WAF facts
  aws_waf_facts:

- name: obtain all facts for a single WAF
  aws_waf_facts:
    name: test_waf
'''

RETURN = '''
wafs:
  description: The WAFs that match the passed arguments
  returned: success
  type: complex
  contains:
    name:
      description: A friendly name or description of the WebACL
      returned: always
      type: str
      sample: test_waf
    default_action:
      description: The action to perform if none of the Rules contained in the WebACL match.
      returned: always
      type: int
      sample: BLOCK
    metric_name:
      description: A friendly name or description for the metrics for this WebACL
      returned: always
      type: str
      sample: test_waf_metric
    rules:
      description: An array that contains the action for each Rule in a WebACL , the priority of the Rule
      returned: always
      type: complex
      contains:
        action:
          description: The action to perform if the Rule matches
          returned: always
          type: str
          sample: BLOCK
        metric_name:
          description: A friendly name or description for the metrics for this Rule
          returned: always
          type: str
          sample: ipblockrule
        name:
          description: A friendly name or description of the Rule
          returned: always
          type: str
          sample: ip_block_rule
        predicates:
          description: The Predicates list contains a Predicate for each
            ByteMatchSet, IPSet, SizeConstraintSet, SqlInjectionMatchSet or XssMatchSet
            object in a Rule
          returned: always
          type: list
          sample:
            [
              {
                "byte_match_set_id": "47b822b5-abcd-1234-faaf-1234567890",
                "byte_match_tuples": [
                  {
                    "field_to_match": {
                      "type": "QUERY_STRING"
                    },
                    "positional_constraint": "STARTS_WITH",
                    "target_string": "bobbins",
                    "text_transformation": "NONE"
                  }
                ],
                "name": "bobbins",
                "negated": false,
                "type": "ByteMatch"
              }
            ]
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.aws.waf import list_web_acls, get_web_acl


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=False),
        )
    )
    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='waf', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    web_acls = list_web_acls(client, module)
    name = module.params['name']
    if name:
        web_acls = [web_acl for web_acl in web_acls if
                    web_acl['Name'] == name]
        if not web_acls:
            module.fail_json(msg="WAF named %s not found" % name)
    module.exit_json(wafs=[get_web_acl(client, module, web_acl['WebACLId'])
                           for web_acl in web_acls])


if __name__ == '__main__':
    main()
