#!/usr/bin/python
# (c) 2016, Pierre Jodouin <pjodouin@virtualcomputing.solutions>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: lambda_event
short_description: Creates, updates or deletes AWS Lambda function event mappings.
description:
    - This module allows the management of AWS Lambda function event source mappings such as DynamoDB and Kinesis stream
      events via the Ansible framework. These event source mappings are relevant only in the AWS Lambda pull model, where
      AWS Lambda invokes the function.
      It is idempotent and supports "Check" mode.  Use module M(lambda) to manage the lambda
      function itself and M(lambda_alias) to manage function aliases.

version_added: "2.2"

author: Pierre Jodouin (@pjodouin), Ryan Brown (@ryansb)
options:
  lambda_function_arn:
    description:
      - The name or ARN of the lambda function.
    required: true
    aliases: ['function_name', 'function_arn']
  state:
    description:
      - Describes the desired state.
    required: true
    default: "present"
    choices: ["present", "absent"]
  alias:
    description:
      - Name of the function alias. Mutually exclusive with C(version).
    required: true
  version:
    description:
      -  Version of the Lambda function. Mutually exclusive with C(alias).
    required: false
  event_source:
    description:
      -  Source of the event that triggers the lambda function.
    required: false
    default: stream
    choices: ['stream']
  source_params:
    description:
      -  Sub-parameters required for event source.
      -  I(== stream event source ==)
      -  C(source_arn) The Amazon Resource Name (ARN) of the Kinesis or DynamoDB stream that is the event source.
      -  C(enabled) Indicates whether AWS Lambda should begin polling the event source. Default is True.
      -  C(batch_size) The largest number of records that AWS Lambda will retrieve from your event source at the
         time of invoking your function. Default is 100.
      -  C(starting_position) The position in the stream where AWS Lambda should start reading.
         Choices are TRIM_HORIZON or LATEST.
    required: true
requirements:
    - boto3
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
---
# Example that creates a lambda event notification for a DynamoDB stream
- hosts: localhost
  gather_facts: no
  vars:
    state: present
  tasks:
  - name: DynamoDB stream event mapping
    lambda_event:
      state: "{{ state | default('present') }}"
      event_source: stream
      function_name: "{{ function_name }}"
      alias: Dev
      source_params:
        source_arn: arn:aws:dynamodb:us-east-1:123456789012:table/tableName/stream/2016-03-19T19:51:37.457
        enabled: True
        batch_size: 100
        starting_position: TRIM_HORIZON

  - name: Show source event
    debug:
      var: lambda_stream_events
'''

RETURN = '''
---
lambda_stream_events:
    description: list of dictionaries returned by the API describing stream event mappings
    returned: success
    type: list
'''

import re
import sys

try:
    import boto3
    from botocore.exceptions import ClientError, ParamValidationError, MissingParametersError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, camel_dict_to_snake_dict, ec2_argument_spec,
                                      get_aws_connection_info)


# ---------------------------------------------------------------------------------------------------
#
#   Helper Functions & classes
#
# ---------------------------------------------------------------------------------------------------


class AWSConnection:
    """
    Create the connection object and client objects as required.
    """

    def __init__(self, ansible_obj, resources, use_boto3=True):

        try:
            self.region, self.endpoint, aws_connect_kwargs = get_aws_connection_info(ansible_obj, boto3=use_boto3)

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

        # set account ID
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


def ordered_obj(obj):
    """
    Order object for comparison purposes

    :param obj:
    :return:
    """

    if isinstance(obj, dict):
        return sorted((k, ordered_obj(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered_obj(x) for x in obj)
    else:
        return obj


def set_api_sub_params(params):
    """
    Sets module sub-parameters to those expected by the boto3 API.

    :param params:
    :return:
    """

    api_params = dict()

    for param in params.keys():
        param_value = params.get(param, None)
        if param_value:
            api_params[pc(param)] = param_value

    return api_params


def validate_params(module, aws):
    """
    Performs basic parameter validation.

    :param module:
    :param aws:
    :return:
    """

    function_name = module.params['lambda_function_arn']

    # validate function name
    if not re.search(r'^[\w\-:]+$', function_name):
        module.fail_json(
            msg='Function name {0} is invalid. Names must contain only alphanumeric characters and hyphens.'.format(function_name)
        )
    if len(function_name) > 64 and not function_name.startswith('arn:aws:lambda:'):
        module.fail_json(msg='Function name "{0}" exceeds 64 character limit'.format(function_name))

    elif len(function_name) > 140 and function_name.startswith('arn:aws:lambda:'):
        module.fail_json(msg='ARN "{0}" exceeds 140 character limit'.format(function_name))

    # check if 'function_name' needs to be expanded in full ARN format
    if not module.params['lambda_function_arn'].startswith('arn:aws:lambda:'):
        function_name = module.params['lambda_function_arn']
        module.params['lambda_function_arn'] = 'arn:aws:lambda:{0}:{1}:function:{2}'.format(aws.region, aws.account_id, function_name)

    qualifier = get_qualifier(module)
    if qualifier:
        function_arn = module.params['lambda_function_arn']
        module.params['lambda_function_arn'] = '{0}:{1}'.format(function_arn, qualifier)

    return


def get_qualifier(module):
    """
    Returns the function qualifier as a version or alias or None.

    :param module:
    :return:
    """

    qualifier = None
    if module.params['version'] > 0:
        qualifier = str(module.params['version'])
    elif module.params['alias']:
        qualifier = str(module.params['alias'])

    return qualifier


# ---------------------------------------------------------------------------------------------------
#
#   Lambda Event Handlers
#
#   This section defines a lambda_event_X function where X is an AWS service capable of initiating
#   the execution of a Lambda function (pull only).
#
# ---------------------------------------------------------------------------------------------------

def lambda_event_stream(module, aws):
    """
    Adds, updates or deletes lambda stream (DynamoDb, Kinesis) event notifications.
    :param module:
    :param aws:
    :return:
    """

    client = aws.client('lambda')
    facts = dict()
    changed = False
    current_state = 'absent'
    state = module.params['state']

    api_params = dict(FunctionName=module.params['lambda_function_arn'])

    # check if required sub-parameters are present and valid
    source_params = module.params['source_params']

    source_arn = source_params.get('source_arn')
    if source_arn:
        api_params.update(EventSourceArn=source_arn)
    else:
        module.fail_json(msg="Source parameter 'source_arn' is required for stream event notification.")

    # check if optional sub-parameters are valid, if present
    batch_size = source_params.get('batch_size')
    if batch_size:
        try:
            source_params['batch_size'] = int(batch_size)
        except ValueError:
            module.fail_json(msg="Source parameter 'batch_size' must be an integer, found: {0}".format(source_params['batch_size']))

    # optional boolean value needs special treatment as not present does not imply False
    source_param_enabled = module.boolean(source_params.get('enabled', 'True'))

    # check if event mapping exist
    try:
        facts = client.list_event_source_mappings(**api_params)['EventSourceMappings']
        if facts:
            current_state = 'present'
    except ClientError as e:
        module.fail_json(msg='Error retrieving stream event notification configuration: {0}'.format(e))

    if state == 'present':
        if current_state == 'absent':

            starting_position = source_params.get('starting_position')
            if starting_position:
                api_params.update(StartingPosition=starting_position)
            else:
                module.fail_json(msg="Source parameter 'starting_position' is required for stream event notification.")

            if source_arn:
                api_params.update(Enabled=source_param_enabled)
            if source_params.get('batch_size'):
                api_params.update(BatchSize=source_params.get('batch_size'))

            try:
                if not module.check_mode:
                    facts = client.create_event_source_mapping(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg='Error creating stream source event mapping: {0}'.format(e))

        else:
            # current_state is 'present'
            api_params = dict(FunctionName=module.params['lambda_function_arn'])
            current_mapping = facts[0]
            api_params.update(UUID=current_mapping['UUID'])
            mapping_changed = False

            # check if anything changed
            if source_params.get('batch_size') and source_params['batch_size'] != current_mapping['BatchSize']:
                api_params.update(BatchSize=source_params['batch_size'])
                mapping_changed = True

            if source_param_enabled is not None:
                if source_param_enabled:
                    if current_mapping['State'] not in ('Enabled', 'Enabling'):
                        api_params.update(Enabled=True)
                        mapping_changed = True
                else:
                    if current_mapping['State'] not in ('Disabled', 'Disabling'):
                        api_params.update(Enabled=False)
                        mapping_changed = True

            if mapping_changed:
                try:
                    if not module.check_mode:
                        facts = client.update_event_source_mapping(**api_params)
                    changed = True
                except (ClientError, ParamValidationError, MissingParametersError) as e:
                    module.fail_json(msg='Error updating stream source event mapping: {0}'.format(e))

    else:
        if current_state == 'present':
            # remove the stream event mapping
            api_params = dict(UUID=facts[0]['UUID'])

            try:
                if not module.check_mode:
                    facts = client.delete_event_source_mapping(**api_params)
                changed = True
            except (ClientError, ParamValidationError, MissingParametersError) as e:
                module.fail_json(msg='Error removing stream source event mapping: {0}'.format(e))

    return camel_dict_to_snake_dict(dict(changed=changed, events=facts))


def main():
    """Produce a list of function suffixes which handle lambda events."""
    this_module = sys.modules[__name__]
    source_choices = ["stream"]

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=False, default='present', choices=['present', 'absent']),
            lambda_function_arn=dict(required=True, default=None, aliases=['function_name', 'function_arn']),
            event_source=dict(required=False, default="stream", choices=source_choices),
            source_params=dict(type='dict', required=True, default=None),
            alias=dict(required=False, default=None),
            version=dict(type='int', required=False, default=0),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['alias', 'version']],
        required_together=[]
    )

    # validate dependencies
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module.')

    aws = AWSConnection(module, ['lambda'])

    validate_params(module, aws)

    this_module_function = getattr(this_module, 'lambda_event_{0}'.format(module.params['event_source'].lower()))

    results = this_module_function(module, aws)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
