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
extends_documentation_fragment: aws
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
      type: string
      sample: test_waf
    default_action:
      description: The action to perform if none of the Rules contained in the WebACL match.
      returned: always
      type: int
      sample: BLOCK
    metric_name:
      description: A friendly name or description for the metrics for this WebACL
      returned: always
      type: string
      sample: test_waf_metric
    rules:
      description: An array that contains the action for each Rule in a WebACL , the priority of the Rule
      returned: always
      type: complex
      contains:
        action:
          description: The action to perform if the Rule matches
          returned: always
          type: string
          sample: BLOCK
        metric_name:
          description: A friendly name or description for the metrics for this Rule
          returned: always
          type: string
          sample: ipblockrule
        name:
          description: A friendly name or description of the Rule
          returned: always
          type: string
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

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, HAS_BOTO3, AWSRetry


try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_rule_with_backoff(client, rule_id):
    return client.get_rule(RuleId=rule_id)


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_byte_match_set_with_backoff(client, byte_match_set_id):
    return client.get_byte_match_set(ByteMatchSetId=byte_match_set_id)['ByteMatchSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_ip_set_with_backoff(client, ip_set_id):
    return client.get_ip_set(IPSetId=ip_set_id)['IPSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_size_constraint_set_with_backoff(client, size_constraint_set_id):
    return client.get_size_constraint_set(SizeConstraintSetId=size_constraint_set_id)['SizeConstraintSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_sql_injection_match_set_with_backoff(client, sql_injection_match_set_id):
    return client.get_sql_injection_match_set(SqlInjectionMatchSetId=sql_injection_match_set_id)['SqlInjectionMatchSet']


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_xss_match_set_with_backoff(client, xss_match_set_id):
    return client.get_xss_match_set(XssMatchSetId=xss_match_set_id)['XssMatchSet']


def get_rule(client, rule_id):
    rule = get_rule_with_backoff(client, rule_id)['Rule']
    match_sets = {
        'ByteMatch': get_byte_match_set_with_backoff,
        'IPMatch': get_ip_set_with_backoff,
        'SizeConstraint': get_size_constraint_set_with_backoff,
        'SqlInjectionMatch': get_sql_injection_match_set_with_backoff,
        'XssMatch': get_xss_match_set_with_backoff
    }
    if 'Predicates' in rule:
        for predicate in rule['Predicates']:
            if predicate['Type'] in match_sets:
                predicate.update(match_sets[predicate['Type']](client, predicate['DataId']))
                # replaced by Id from the relevant MatchSet
                del(predicate['DataId'])
    return rule


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def get_web_acl_with_backoff(client, web_acl_id):
    return client.get_web_acl(WebACLId=web_acl_id)


def get_web_acl(client, module, web_acl_id):
    try:
        web_acl = get_web_acl_with_backoff(client, web_acl_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't obtain web acl",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    if web_acl['WebACL']:
        try:
            for rule in web_acl['WebACL']['Rules']:
                rule.update(get_rule(client, rule['RuleId']))
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't obtain web acl rule",
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    return camel_dict_to_snake_dict(web_acl['WebACL'])


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_web_acls_with_backoff(client):
    paginator = client.get_paginator('list_web_acls')
    return paginator.paginate().build_full_result()['WebACLs']


def list_web_acls(client, module):
    try:
        return list_web_acls_with_backoff(client)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't obtain web acls",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=False),
        )
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required.')
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='waf', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Can't authorize connection - " + str(e))

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
