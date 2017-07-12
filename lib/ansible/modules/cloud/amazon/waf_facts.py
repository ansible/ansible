#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
DOCUMENTATION = '''
module: waf_facts
short_description: Retrieve facts for WAF ACLs, Rule , Conditions and Filters.
description:
  - Read the AWS documentation for WAF
    U(https://aws.amazon.com/documentation/waf/)
version_added: "2.1"

author: Mike Mochan(@mmochan)
extends_documentation_fragment: aws
'''

EXAMPLES = '''


'''
RETURN = '''
task:
  description: The result of the xxxx, or xxxx action.
  returned: success
  type: dictionary
'''

try:
    import json
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def list_rules(client):
    try:
        return client.list_rules(Limit=10)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e)) 


def get_rule(rule_id, client):
    try:
        return client.get_rule(RuleId=rule_id)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e)) 


def get_web_acl(client, module):
    changed = False
    web_acls = list_web_acls(client, module)[1]
    try:
        our_webacl = None
        our_webacl = next((item for item in web_acls if item.get("Name") == module.params.get('name')))
    except StopIteration:
        pass
    if our_webacl:
        try:
            web_acl = client.get_web_acl(WebACLId=our_webacl['WebACLId'])
            if web_acl['WebACL']:
                web_acl['WebACL']['rule_conditions'] = list()
                for rule in web_acl['WebACL']['Rules']:
                    rule = get_rule(rule['RuleId'], client)
                    web_acl['WebACL']['rule_conditions'].append([rule['Rule']])
                return changed, web_acl['WebACL']
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e)) 
    else:
        return changed, {'waf': 'Not Found'}


def list_web_acls(client, module):
    changed = False
    try:
        web_acl = client.list_web_acls(Limit=10)
        return changed, web_acl['WebACLs']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e)) 


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=False),
        web_acl_id=dict(require=False),
        state=dict(default='list', choices=['get', 'list']),
        ),
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='json and boto3 is required.')
    state = module.params.get('state').lower()
    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='waf', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError, e:
        module.fail_json(msg="Can't authorize connection - "+str(e))
    
    invocations = {
        "get": get_web_acl,
        "list": list_web_acls
    }
    if state == 'get':
        (changed, results) = invocations[state](client, module)
        module.exit_json(changed=changed, waf=results)
    if state == 'list':
        (changed, results) = invocations[state](client, module)
        module.exit_json(changed=changed, wafs=results)      

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
