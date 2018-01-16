#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: lambda_alias
short_description: Creates, updates or deletes AWS Lambda function aliases.
description:
    - This module allows the management of AWS Lambda functions aliases via the Ansible
      framework.  It is idempotent and supports "Check" mode.    Use module M(lambda) to manage the lambda function
      itself and M(lambda_event) to manage event source mappings.

version_added: "2.2"

author: Pierre Jodouin (@pjodouin), Ryan Scott Brown (@ryansb)
options:
  function_name:
    description:
      - The name of the function alias.
    required: true
  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]
  name:
    description:
      - Name of the function alias.
    required: true
    aliases: ['alias_name']
  description:
    description:
      - A short, user-defined function alias description.
    required: false
  version:
    description:
      -  Version associated with the Lambda function alias.
         A value of 0 (or omitted parameter) sets the alias to the $LATEST version.
    required: false
    aliases: ['function_version']
requirements:
    - boto3
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
---
# Simple example to create a lambda function and publish a version
- hosts: localhost
  gather_facts: no
  vars:
    state: present
    project_folder: /path/to/deployment/package
    deployment_package: lambda.zip
    account: 123456789012
    production_version: 5
  tasks:
  - name: AWS Lambda Function
    lambda:
      state: "{{ state | default('present') }}"
      name: myLambdaFunction
      publish: True
      description: lambda function description
      code_s3_bucket: package-bucket
      code_s3_key: "lambda/{{ deployment_package }}"
      local_path: "{{ project_folder }}/{{ deployment_package }}"
      runtime: python2.7
      timeout: 5
      handler: lambda.handler
      memory_size: 128
      role: "arn:aws:iam::{{ account }}:role/API2LambdaExecRole"

  - name: show results
    debug:
      var: lambda_facts

# The following will set the Dev alias to the latest version ($LATEST) since version is omitted (or = 0)
  - name: "alias 'Dev' for function {{ lambda_facts.FunctionName }} "
    lambda_alias:
      state: "{{ state | default('present') }}"
      function_name: "{{ lambda_facts.FunctionName }}"
      name: Dev
      description: Development is $LATEST version

# The QA alias will only be created when a new version is published (i.e. not = '$LATEST')
  - name: "alias 'QA' for function {{ lambda_facts.FunctionName }} "
    lambda_alias:
      state: "{{ state | default('present') }}"
      function_name: "{{ lambda_facts.FunctionName }}"
      name: QA
      version: "{{ lambda_facts.Version }}"
      description: "QA is version {{ lambda_facts.Version }}"
    when: lambda_facts.Version != "$LATEST"

# The Prod alias will have a fixed version based on a variable
  - name: "alias 'Prod' for function {{ lambda_facts.FunctionName }} "
    lambda_alias:
      state: "{{ state | default('present') }}"
      function_name: "{{ lambda_facts.FunctionName }}"
      name: Prod
      version: "{{ production_version }}"
      description: "Production is version {{ production_version }}"
'''

RETURN = '''
---
alias_arn:
    description: Full ARN of the function, including the alias
    returned: success
    type: string
    sample: arn:aws:lambda:us-west-2:123456789012:function:myFunction:dev
description:
    description: A short description of the alias
    returned: success
    type: string
    sample: The development stage for my hot new app
function_version:
    description: The qualifier that the alias refers to
    returned: success
    type: string
    sample: $LATEST
name:
    description: The name of the alias assigned
    returned: success
    type: string
    sample: dev
'''

import re

try:
    import boto3
    from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec,
                                      get_aws_connection_info)


class AWSConnection:
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, boto3_=True):

        try:
            self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=boto3_)

            self.resource_client = dict()
            if not resources:
                resources = ['lambda']

            resources.append('iam')

            for resource in resources:
                aws_connect_kwargs.update(dict(region=self.region,
                                               endpoint=self.endpoint,
                                               conn_type='client',
                                               resource=resource
                                               ))
                self.resource_client[resource] = boto3_conn(ansible_obj, **aws_connect_kwargs)

            # if region is not provided, then get default profile/session region
            if not self.region:
                self.region = self.resource_client['lambda'].meta.region_name

        except (ClientError, ParamValidationError, MissingParametersError) as e:
            ansible_obj.fail_json(msg="Unable to connect, authorize or access resource: {0}".format(e))

        try:
            self.account_id = self.resource_client['iam'].get_user()['User']['Arn'].split(':')[4]
        except (ClientError, ValueError, KeyError, IndexError):
            self.account_id = ''

    def client(self, resource='lambda'):
        return self.resource_client[resource]


def pc(key):
    """
    Changes python key into Pascale case equivalent. For example, 'this_function_name' becomes 'ThisFunctionName'.

    :param key:
    :return:
    """

    return "".join([token.capitalize() for token in key.split('_')])


def set_api_params(module, module_params):
    """
    Sets module parameters to those expected by the boto3 API.

    :param module:
    :param module_params:
    :return:
    """

    api_params = dict()

    for param in module_params:
        module_param = module.params.get(param, None)
        if module_param:
            api_params[pc(param)] = module_param

    return api_params


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return:
    """

    function_name = module.params['function_name']

    # validate function name
    if not re.search(r'^[\w\-:]+$', function_name):
        module.fail_json(
            msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
        )
    if len(function_name) > 64:
        module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

    #  if parameter 'function_version' is zero, set it to $LATEST, else convert it to a string
    if module.params['function_version'] == 0:
        module.params['function_version'] = '$LATEST'
    else:
        module.params['function_version'] = str(module.params['function_version'])

    return


def get_lambda_alias(module, aws):
    """
    Returns the lambda function alias if it exists.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return:
    """

    client = aws.client('lambda')

    # set API parameters
    api_params = set_api_params(module, ('function_name', 'name'))

    # check if alias exists and get facts
    try:
        results = client.get_alias(**api_params)

    except (ClientError, ParamValidationError, MissingParametersError) as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            results = None
        else:
            module.fail_json(msg='Error retrieving function alias: {0}'.format(e))

    return results


def lambda_alias(module, aws):
    """
    Adds, updates or deletes lambda function aliases.

    :param module: Ansible module reference
    :param aws: AWS client connection
    :return dict:
    """
    client = aws.client('lambda')
    results = dict()
    changed = False
    current_state = 'absent'
    state = module.params['state']

    facts = get_lambda_alias(module, aws)
    if facts:
        current_state = 'present'

    if state == 'present':
        if current_state == 'present':

            # check if alias has changed -- only version and description can change
            alias_params = ('function_version', 'description')
            for param in alias_params:
                if module.params.get(param) != facts.get(pc(param)):
                    changed = True
                    break

            if changed:
                api_params = set_api_params(module, ('function_name', 'name'))
                api_params.update(set_api_params(module, alias_params))

                if not module.check_mode:
                    try:
                        results = client.update_alias(**api_params)
                    except (ClientError, ParamValidationError, MissingParametersError) as e:
                        module.fail_json(msg='Error updating function alias: {0}'.format(e))

        else:
            # create new function alias
            api_params = set_api_params(module, ('function_name', 'name', 'function_version', 'description'))

            try:
                if not module.check_mode:
                    results = client.create_alias(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg='Error creating function alias: {0}'.format(e))

    else:  # state = 'absent'
        if current_state == 'present':
            # delete the function
            api_params = set_api_params(module, ('function_name', 'name'))

            try:
                if not module.check_mode:
                    results = client.delete_alias(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg='Error deleting function alias: {0}'.format(e))

    return dict(changed=changed, **dict(results or facts))


def main():
    """
    Main entry point.

    :return dict: ansible facts
    """
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            function_name=dict(required=True, default=None),
            name=dict(required=True, default=None, aliases=['alias_name']),
            function_version=dict(type='int', required=False, default=0, aliases=['version']),
            description=dict(required=False, default=None),
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

    aws = AWSConnection(module, ['lambda'])

    validate_params(module, aws)

    results = lambda_alias(module, aws)

    module.exit_json(**camel_dict_to_snake_dict(results))


if __name__ == '__main__':
    main()
