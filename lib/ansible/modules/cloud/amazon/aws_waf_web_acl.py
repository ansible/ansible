#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
module: aws_waf_web_acl
short_description: create and delete WAF Web ACLs
description:
  - Read the AWS documentation for WAF
    U(https://aws.amazon.com/documentation/waf/)
version_added: "2.5"

author:
  - Mike Mochan (@mmochan)
  - Will Thames (@willthames)
extends_documentation_fragment:
  - aws
  - ec2
options:
    name:
        description: Name of the Web Application Firewall ACL to manage
        required: yes
    default_action:
        description: The action that you want AWS WAF to take when a request doesn't
          match the criteria specified in any of the Rule objects that are associated with the WebACL
        choices:
        - block
        - allow
        - count
    state:
        description: whether the Web ACL should be present or absent
        choices:
        - present
        - absent
        default: present
    metric_name:
        description:
        - A friendly name or description for the metrics for this WebACL
        - The name can contain only alphanumeric characters (A-Z, a-z, 0-9); the name can't contain whitespace.
        - You can't change metric_name after you create the WebACL
        - Metric name will default to I(name) with disallowed characters stripped out
    rules:
        description:
        - A list of rules that the Web ACL will enforce.
        - Each rule must contain I(name), I(action), I(priority) keys.
        - Priorities must be unique, but not necessarily consecutive. Lower numbered priorities are evalauted first.
        - The I(type) key can be passed as C(rate_based), it defaults to C(regular)

    purge_rules:
        description:
        - Whether to remove rules that aren't passed with C(rules).
        default: False
        type: bool
'''

EXAMPLES = '''
  - name: create web ACL
    aws_waf_web_acl:
      name: my_web_acl
      rules:
        - name: my_rule
          priority: 1
          action: block
      default_action: block
      purge_rules: yes
      state: present

  - name: delete the web acl
    aws_waf_web_acl:
      name: my_web_acl
      state: absent
'''

RETURN = '''
web_acl:
  description: contents of the Web ACL
  returned: always
  type: complex
  contains:
    default_action:
      description: Default action taken by the Web ACL if no rules match
      returned: always
      type: dict
      sample:
        type: BLOCK
    metric_name:
      description: Metric name used as an identifier
      returned: always
      type: str
      sample: mywebacl
    name:
      description: Friendly name of the Web ACL
      returned: always
      type: str
      sample: my web acl
    rules:
      description: List of rules
      returned: always
      type: complex
      contains:
        action:
          description: Action taken by the WAF when the rule matches
          returned: always
          type: complex
          sample:
            type: ALLOW
        priority:
          description: priority number of the rule (lower numbers are run first)
          returned: always
          type: int
          sample: 2
        rule_id:
          description: Rule ID
          returned: always
          type: str
          sample: a6fc7ab5-287b-479f-8004-7fd0399daf75
        type:
          description: Type of rule (either REGULAR or RATE_BASED)
          returned: always
          type: str
          sample: REGULAR
    web_acl_id:
      description: Unique identifier of Web ACL
      returned: always
      type: str
      sample: 10fff965-4b6b-46e2-9d78-24f6d2e2d21c
'''

try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule

import re

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.waiters import get_waiter
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, camel_dict_to_snake_dict
from ansible.module_utils.aws.waf import list_rules_with_backoff, list_web_acls_with_backoff, run_func_with_change_token_backoff


def get_web_acl_by_name(client, module, name):
    acls = [d['WebACLId'] for d in list_web_acls(client, module) if d['Name'] == name]
    if acls:
        return acls[0]
    else:
        return acls


def create_rule_lookup(client, module):
    try:
        rules = list_rules_with_backoff(client)
        return dict((rule['Name'], rule) for rule in rules)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not list rules')


def get_web_acl(client, module, web_acl_id):
    try:
        return client.get_web_acl(WebACLId=web_acl_id)['WebACL']
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not get Web ACL with id %s' % web_acl_id)


def list_web_acls(client, module,):
    try:
        return list_web_acls_with_backoff(client)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not get Web ACLs')


def find_and_update_web_acl(client, module, web_acl_id):
    acl = get_web_acl(client, module, web_acl_id)
    rule_lookup = create_rule_lookup(client, module)
    existing_rules = acl['Rules']
    desired_rules = [{'RuleId': rule_lookup[rule['name']]['RuleId'],
                      'Priority': rule['priority'],
                      'Action': {'Type': rule['action'].upper()},
                      'Type': rule.get('type', 'regular').upper()}
                     for rule in module.params['rules']]
    missing = [rule for rule in desired_rules if rule not in existing_rules]
    extras = []
    if module.params['purge_rules']:
        extras = [rule for rule in existing_rules if rule not in desired_rules]

    insertions = [format_for_update(rule, 'INSERT') for rule in missing]
    deletions = [format_for_update(rule, 'DELETE') for rule in extras]
    changed = bool(insertions + deletions)

    # Purge rules before adding new ones in case a deletion shares the same
    # priority as an insertion.
    params = {
        'WebACLId': acl['WebACLId'],
        'DefaultAction': acl['DefaultAction']
    }
    change_tokens = []
    if deletions:
        try:
            params['Updates'] = deletions
            result = run_func_with_change_token_backoff(client, module, params, client.update_web_acl)
            change_tokens.append(result['ChangeToken'])
            get_waiter(
                client, 'change_token_in_sync',
            ).wait(
                ChangeToken=result['ChangeToken']
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not update Web ACL')
    if insertions:
        try:
            params['Updates'] = insertions
            result = run_func_with_change_token_backoff(client, module, params, client.update_web_acl)
            change_tokens.append(result['ChangeToken'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not update Web ACL')
    if change_tokens:
        for token in change_tokens:
            get_waiter(
                client, 'change_token_in_sync',
            ).wait(
                ChangeToken=token
            )
    if changed:
        acl = get_web_acl(client, module, web_acl_id)
    return changed, acl


def format_for_update(rule, action):
    return dict(
        Action=action,
        ActivatedRule=dict(
            Priority=rule['Priority'],
            RuleId=rule['RuleId'],
            Action=dict(
                Type=rule['Action']['Type']
            )
        )
    )


def remove_rules_from_web_acl(client, module, web_acl_id):
    acl = get_web_acl(client, module, web_acl_id)
    deletions = [format_for_update(rule, 'DELETE') for rule in acl['Rules']]
    try:
        params = {'WebACLId': acl['WebACLId'], 'DefaultAction': acl['DefaultAction'], 'Updates': deletions}
        run_func_with_change_token_backoff(client, module, params, client.update_web_acl)
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg='Could not remove rule')


def ensure_web_acl_present(client, module):
    changed = False
    result = None
    name = module.params['name']
    web_acl_id = get_web_acl_by_name(client, module, name)
    if web_acl_id:
        (changed, result) = find_and_update_web_acl(client, module, web_acl_id)
    else:
        metric_name = module.params['metric_name']
        if not metric_name:
            metric_name = re.sub(r'[^A-Za-z0-9]', '', module.params['name'])
        default_action = module.params['default_action'].upper()
        try:
            params = {'Name': name, 'MetricName': metric_name, 'DefaultAction': {'Type': default_action}}
            new_web_acl = run_func_with_change_token_backoff(client, module, params, client.create_web_acl)
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not create Web ACL')
        (changed, result) = find_and_update_web_acl(client, module, new_web_acl['WebACL']['WebACLId'])
    return changed, result


def ensure_web_acl_absent(client, module):
    web_acl_id = get_web_acl_by_name(client, module, module.params['name'])
    if web_acl_id:
        web_acl = get_web_acl(client, module, web_acl_id)
        if web_acl['Rules']:
            remove_rules_from_web_acl(client, module, web_acl_id)
        try:
            run_func_with_change_token_backoff(client, module, {'WebACLId': web_acl_id}, client.delete_web_acl, wait=True)
            return True, {}
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg='Could not delete Web ACL')
    return False, {}


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True),
            default_action=dict(choices=['block', 'allow', 'count']),
            metric_name=dict(),
            state=dict(default='present', choices=['present', 'absent']),
            rules=dict(type='list'),
            purge_rules=dict(type='bool', default=False)
        ),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['state', 'present', ['default_action', 'rules']]])
    state = module.params.get('state')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client = boto3_conn(module, conn_type='client', resource='waf', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    if state == 'present':
        (changed, results) = ensure_web_acl_present(client, module)
    else:
        (changed, results) = ensure_web_acl_absent(client, module)

    module.exit_json(changed=changed, web_acl=camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
