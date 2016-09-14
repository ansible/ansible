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

import datetime
import sys

try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


DOCUMENTATION = '''
---
module: lambda_facts
short_description: Gathers AWS Lambda function details as Ansible facts
description:
  - Gathers various details related to Lambda functions, including aliases, versions and event source mappings.
    Use module M(lambda) to manage the lambda function itself, M(lambda_alias) to manage function aliases and
    M(lambda_event) to manage lambda event source mappings.

version_added: "2.2"

options:
  query:
    description:
      - Specifies the resource type for which to gather facts.  Leave blank to retrieve all facts.
    required: true
    choices: [ "aliases", "all", "config", "mappings", "policy", "versions" ]
    default: "all"
  function_name:
    description:
      - The name of the lambda function for which facts are requested.
    required: false
    default: null
    aliases: [ "function", "name"]
  event_source_arn:
    description:
      - For query type 'mappings', this is the Amazon Resource Name (ARN) of the Amazon Kinesis or DynamoDB stream.
    default: null
    required: false
author: Pierre Jodouin (@pjodouin)
requirements:
    - boto3
extends_documentation_fragment:
    - aws

'''

EXAMPLES = '''
---
# Simple example of listing all info for a function
- name: List all for a specific function
  lambda_facts:
    query: all
    function_name: myFunction
  register: my_function_details
# List all versions of a function
- name: List function versions
  lambda_facts:
    query: versions
    function_name: myFunction
  register: my_function_versions
# List all lambda function versions
- name: List all function
  lambda_facts:
    query: all
    max_items: 20
- name: show Lambda facts
  debug: var=lambda_facts
'''

RETURN = '''
---
lambda_facts:
    description: lambda facts
    returned: success
    type: dict
lambda_facts.function:
    description: lambda function list
    returned: success
    type: dict
lambda_facts.function.TheName:
    description: lambda function information, including event, mapping, and version information
    returned: success
    type: dict
'''


def fix_return(node):
    """
    fixup returned dictionary

    :param node:
    :return:
    """

    if isinstance(node, datetime.datetime):
        node_value = str(node)

    elif isinstance(node, list):
        node_value = [fix_return(item) for item in node]

    elif isinstance(node, dict):
        node_value = dict([(item, fix_return(node[item])) for item in node.keys()])

    else:
        node_value = node

    return node_value


def alias_details(client, module):
    """
    Returns list of aliases for a specified function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')
        try:
            lambda_facts.update(aliases=client.list_aliases(FunctionName=function_name, **params)['Aliases'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                lambda_facts.update(aliases=[])
            else:
                module.fail_json(msg='Unable to get {0} aliases, error: {1}'.format(function_name, e))
    else:
        module.fail_json(msg='Parameter function_name required for query=aliases.')

    return {function_name: camel_dict_to_snake_dict(lambda_facts)}


def all_details(client, module):
    """
    Returns all lambda related facts.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    if module.params.get('max_items') or module.params.get('next_marker'):
        module.fail_json(msg='Cannot specify max_items nor next_marker for query=all.')

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        lambda_facts[function_name] = {}
        lambda_facts[function_name].update(config_details(client, module)[function_name])
        lambda_facts[function_name].update(alias_details(client, module)[function_name])
        lambda_facts[function_name].update(policy_details(client, module)[function_name])
        lambda_facts[function_name].update(version_details(client, module)[function_name])
        lambda_facts[function_name].update(mapping_details(client, module)[function_name])
    else:
        lambda_facts.update(config_details(client, module))

    return lambda_facts


def config_details(client, module):
    """
    Returns configuration details for one or all lambda functions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        try:
            lambda_facts.update(client.get_function_configuration(FunctionName=function_name))
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                lambda_facts.update(function={})
            else:
                module.fail_json(msg='Unable to get {0} configuration, error: {1}'.format(function_name, e))
    else:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(function_list=client.list_functions(**params)['Functions'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                lambda_facts.update(function_list=[])
            else:
                module.fail_json(msg='Unable to get function list, error: {0}'.format(e))

        functions = dict()
        for func in lambda_facts.pop('function_list', []):
            functions[func['FunctionName']] = camel_dict_to_snake_dict(func)
        return functions

    return {function_name: camel_dict_to_snake_dict(lambda_facts)}


def mapping_details(client, module):
    """
    Returns all lambda event source mappings.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_facts = dict()
    params = dict()
    function_name = module.params.get('function_name')

    if function_name:
        params['FunctionName'] = module.params.get('function_name')

    if module.params.get('event_source_arn'):
        params['EventSourceArn'] = module.params.get('event_source_arn')

    if module.params.get('max_items'):
        params['MaxItems'] = module.params.get('max_items')

    if module.params.get('next_marker'):
        params['Marker'] = module.params.get('next_marker')

    try:
        lambda_facts.update(mappings=client.list_event_source_mappings(**params)['EventSourceMappings'])
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            lambda_facts.update(mappings=[])
        else:
            module.fail_json(msg='Unable to get source event mappings, error: {0}'.format(e))

    if function_name:
        return {function_name: camel_dict_to_snake_dict(lambda_facts)}

    return camel_dict_to_snake_dict(lambda_facts)


def policy_details(client, module):
    """
    Returns policy attached to a lambda function.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    if module.params.get('max_items') or module.params.get('next_marker'):
        module.fail_json(msg='Cannot specify max_items nor next_marker for query=policy.')

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        try:
            # get_policy returns a JSON string so must convert to dict before reassigning to its key
            lambda_facts.update(policy=json.loads(client.get_policy(FunctionName=function_name)['Policy']))
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                lambda_facts.update(policy={})
            else:
                module.fail_json(msg='Unable to get {0} policy, error: {1}'.format(function_name, e))
    else:
        module.fail_json(msg='Parameter function_name required for query=policy.')

    return {function_name: camel_dict_to_snake_dict(lambda_facts)}


def version_details(client, module):
    """
    Returns all lambda function versions.

    :param client: AWS API client reference (boto3)
    :param module: Ansible module reference
    :return dict:
    """

    lambda_facts = dict()

    function_name = module.params.get('function_name')
    if function_name:
        params = dict()
        if module.params.get('max_items'):
            params['MaxItems'] = module.params.get('max_items')

        if module.params.get('next_marker'):
            params['Marker'] = module.params.get('next_marker')

        try:
            lambda_facts.update(versions=client.list_versions_by_function(FunctionName=function_name, **params)['Versions'])
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                lambda_facts.update(versions=[])
            else:
                module.fail_json(msg='Unable to get {0} versions, error: {1}'.format(function_name, e))
    else:
        module.fail_json(msg='Parameter function_name required for query=versions.')

    return {function_name: camel_dict_to_snake_dict(lambda_facts)}


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            function_name=dict(required=False, default=None, aliases=['function', 'name']),
            query=dict(required=False, choices=['aliases', 'all', 'config', 'mappings', 'policy',  'versions'], default='all'),
            event_source_arn=dict(required=False, default=None)
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[],
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    # validate function_name if present
    function_name = module.params['function_name']
    if function_name:
        if not re.search("^[\w\-:]+$", function_name):
            module.fail_json(
                msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
            )
        if len(function_name) > 64:
            module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

    try:
        region, endpoint, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        aws_connect_kwargs.update(dict(region=region,
                                       endpoint=endpoint,
                                       conn_type='client',
                                       resource='lambda'
                                       ))
        client = boto3_conn(module, **aws_connect_kwargs)
    except ClientError as e:
        module.fail_json(msg="Can't authorize connection - {0}".format(e))

    this_module = sys.modules[__name__]

    invocations = dict(
        aliases='alias_details',
        all='all_details',
        config='config_details',
        mappings='mapping_details',
        policy='policy_details',
        versions='version_details',
    )

    this_module_function = getattr(this_module, invocations[module.params['query']])
    all_facts = fix_return(this_module_function(client, module))

    results = dict(ansible_facts={'lambda_facts': {'function': all_facts}}, changed=False)

    if module.check_mode:
        results['msg'] = 'Check mode set but ignored for fact gathering only.'

    module.exit_json(**results)


# ansible import module(s) kept at ~eof as recommended
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
