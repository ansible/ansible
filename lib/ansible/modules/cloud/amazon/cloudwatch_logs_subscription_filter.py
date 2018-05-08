#!/usr/bin/python

# Copyright: (c) 2018, Rob White (@wimnat)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cloudwatch_logs_subscription_filter
short_description: Manage an AWS CloudWatch Logs subscription filter.
description:
    - Manage an AWS CloudWatch Logs subscription filter. See
      U(https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/SubscriptionFilters.html) for details.
version_added: "2.6"
requirements: [ boto3 ]
author: "Rob White (@wimnat)"
options:
  destination_arn:
    description:
      - The ARN of the destination to deliver matching log events to.
    required: false
  distribution:
    description:
      - The method used to distribute log data to the destination. By default log data is grouped by log stream, but the grouping
        can be set to random for a more even distribution. This property is only applicable when the destination is an Amazon Kinesis stream.
    required: false
    default: by_log_stream
    choices: ['random', 'by_log_stream']
  filter_name:
    description:
      - A name for the subscription filter. If you are updating an existing filter, you must specify the correct name in filter_name,
        otherwise, the call fails (unless I(force_update) is specified).
    required: true
  filter_pattern:
    description:
      - A filter pattern for subscribing to a filtered stream of log events.
    required: false
  force_update:
    description:
      - Usually if I(filter_name) does not match then the module will fail because only one subscription is allowed. By setting
        I(force_update) to yes then the existing subscription will be automatically be removed allowing the new one to be added.
    required: false
    default: no
    type: bool
  log_group_name:
    description:
      - The name of the log group.
    required: true
  role_arn:
    description:
      - The ARN of an IAM role that grants CloudWatch Logs permissions to deliver ingested log events to the destination stream.
        You don't need to provide the ARN when you are working with a logical destination for cross-account delivery.
    required: false
  state:
    description:
      - Add or remove the CloudWatch Logs subscription filter.
    required: true
    choices: [ 'present', 'absent' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Add a CloudWatch Logs subscription filter
- cloudwatch_logs_subscription_filter:
    destination_arn: arn:aws:lambda:ap-southeast-2:0123456789:function:my-destination-lambda
    filter_name: cloudwatch-logs-trigger
    filter_pattern: ""
    force_update: yes
    log_group_name: /aws/lambda/my-lambda
    state: present

# Remove a CloudWatch Logs subscription filter
- cloudwatch_logs_subscription_filter:
    filter_name: cloudwatch-logs-trigger
    log_group_name: /aws/lambda/my-lambda
    state: absent

'''

RETURN = '''
creation_time:
    description: The creation time of the subscription filter, expressed as the number of milliseconds after Jan 1, 1970 00:00:00 UTC.
    returned: when state is present
    type: string
    sample: 1525764318
destination_arn:
    description: The Amazon Resource Name (ARN) of the destination.
    returned: when state is present
    type: string
    sample: arn:aws:lambda:ap-southeast-2:0123456789:function:my-destination-lambda
distribution:
    description: The method used to distribute log data to the destination, which can be either random or grouped by log stream.
    returned: when state is present
    type: string
    sample: random
log_group_name:
    description: The name of the log group.
    returned: when state is present
    type: string
    sample: /aws/lambda/my-lambda
filter_name:
    description: The name of the subscription filter.
    returned: when state is present
    type: string
    sample: cloudwatch-logs-trigger
filter_pattern:
    description: A symbolic description of how CloudWatch Logs should interpret the data in each log event.
    returned: when state is present
    type: string
    sample: "{$.userIdentity.type = Root}"
role_arn:
    description: The ARN of an IAM role that grants CloudWatch Logs permissions to deliver ingested log events to the destination stream.
    returned: when state is present
    type: string
    sample: arn:aws:iam::0123456789:role/Administrator

'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

# Non-ansible imports
try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass


def _get_cw_subscription_filter(connection, module):
    """
    Get the subscription filter of a particular CloudWatch Log Group.

    We only return the first item here - this is all AWS supports (8 May 18)

    :param connection: AWS boto3 logs connection
    :param module: Ansible module
    :return: boto3 CloudWatch logs subscription filter dict or None if not found
    """

    log_group_name = module.params.get("log_group_name")

    try:
        cw_subscription_filters = connection.describe_subscription_filters(logGroupName=log_group_name)['subscriptionFilters']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    if len(cw_subscription_filters) == 0:
        return None
    else:
        return cw_subscription_filters[0]


def _compare_cw_subscription_filter_params(user_params, current_params):
    """
    Compare subscription filter params. If there is a difference, return True immediately else return False

    :param user_params: the subscription filter parameters passed by the user
    :param current_params: the subscription filter parameters currently configured
    :return: True if any parameter is mismatched else False
    """

    if user_params['destinationArn'] != current_params['destinationArn']:
        return True
    if user_params['distribution'] != current_params['distribution']:
        return True
    if user_params['filterPattern'] != current_params['filterPattern']:
        return True
    if user_params['filterName'] != current_params['filterName']:
        return True

    return False


def create_or_update_cw_subscription_filter(connection, module, cw_subscription_filter):
    """
    Create or update a CloudWatch Logs subscription filter

    :param connection: AWS boto3 logs connection
    :param module: Ansible module
    :param cw_subscription_filter: a dict of subscription filter parameters or None
    :return:
    """

    changed = False
    do_put_subscription_filter = False
    force_update = module.params.get("force_update")
    params = dict()
    params['destinationArn'] = module.params.get("destination_arn")
    if module.params.get("distribution") == 'by_log_stream':
        params['distribution'] = 'ByLogStream'
    elif module.params.get("distribution") == 'random':
        params['distribution'] = 'Random'
    params['filterName'] = module.params.get("filter_name")
    params['filterPattern'] = module.params.get("filter_pattern")
    params['logGroupName'] = module.params.get("log_group_name")
    if module.params.get("role_arn") is not None:
        params['roleArn'] = module.params.get("role_arn")

    # If cw_subscription_filter is not None then check if it needs to be modified, else create it
    if cw_subscription_filter:
        # Before we compare other params, check the filter name first, if it's different and the
        # force parameter has been passed then delete the current subscription.
        if params['filterName'] != cw_subscription_filter['filterName'] and force_update:
            delete_cw_subscription_filter(connection, module, cw_subscription_filter, cw_subscription_filter['filterName'])
            do_put_subscription_filter = True
        elif _compare_cw_subscription_filter_params(params, cw_subscription_filter):
            do_put_subscription_filter = True
    else:
        do_put_subscription_filter = True

    if do_put_subscription_filter:
        try:
            connection.put_subscription_filter(**params)
            changed = True
        except (BotoCoreError, ClientError) as e:
            if e.response['Error']['Code'] == 'LimitExceededException':
                module.fail_json_aws(e, "You can only have one subscription per Log Group. You can override using force_update parameter.")
            else:
                module.fail_json_aws(e)

    # If changed, get the subscription filter again
    if changed:
        cw_subscription_filter = _get_cw_subscription_filter(connection, module)

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(cw_subscription_filter))


def delete_cw_subscription_filter(connection, module, cw_subscription_filter, current_filter_name=None):
    """
    Delete a CloudWatch Logs subscription filter

    :param connection: AWS boto3 logs connection
    :param module: Ansible module
    :param cw_subscription_filter: a dict of subscription filter parameters or None
    :param current_filter_name: the filter name currently set in AWS (might differ from what the user has passed)
    :return:
    """

    changed = False
    params = dict()
    # If we've been passed current_filter_name then use this for delete rather than user passed param
    if current_filter_name is not None:
        params['filterName'] = current_filter_name
    else:
        params['filterName'] = module.params.get("filter_name")
    params['logGroupName'] = module.params.get("log_group_name")

    if cw_subscription_filter:
        try:
            connection.delete_subscription_filter(**params)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    return changed


def main():

    argument_spec = (
        dict(
            destination_arn=dict(type='str'),
            distribution=dict(type='str', default='by_log_stream', choices=['random', 'by_log_stream']),
            filter_name=dict(type='str', required=True),
            filter_pattern=dict(type='str'),
            force_update=dict(type='bool', default=False),
            log_group_name=dict(type='str', required=True),
            role_arn=dict(type='str'),
            state=dict(required=True, choices=['present', 'absent'], type='str')
        )
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[
                                  ('state', 'present', ['distribution', 'filter_pattern',
                                                        'destination_arn'])
                              ]
                              )

    connection = module.client('logs')

    cw_subscription_filter = _get_cw_subscription_filter(connection, module)

    if module.params.get("state") == 'present':
        create_or_update_cw_subscription_filter(connection, module, cw_subscription_filter)
    else:
        changed = delete_cw_subscription_filter(connection, module, cw_subscription_filter)
        module.exit_json(changed=changed)

if __name__ == '__main__':
    main()
