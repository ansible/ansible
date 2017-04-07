#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'certified'}


DOCUMENTATION = """
module: ec2_metric_alarm
short_description: "Create/update or delete AWS Cloudwatch 'metric alarms'"
description:
 - Can create or delete AWS metric alarms.
 - Metrics you wish to alarm on must already exist.
version_added: "1.6"
author: "Zacharie Eakin (@zeekin)"
options:
    state:
        description:
          - register or deregister the alarm
        required: true
        choices:
          - 'present'
          - 'absent'
    name:
        description:
          - Unique name for the alarm
        required: true
    metric:
        description:
          - Name of the monitored metric (e.g. CPUUtilization)
          - Metric must already exist
        required: false
    namespace:
        description:
          - Name of the appropriate namespace ('AWS/EC2', 'System/Linux', etc.), which determines the category it will appear under in cloudwatch
        required: false
    statistic:
        description:
          - Operation applied to the metric
          - Works in conjunction with period and evaluation_periods to determine the comparison value
        required: false
        choices:
          - 'SampleCount'
          - 'Average'
          - 'Sum'
          - 'Minimum'
          - 'Maximum'
    comparison:
        description:
          - Determines how the threshold value is compared
        required: false
        choices:
          - 'LessThanOrEqualToThreshold'
          - 'LessThanThreshold'
          - 'GreaterThanThreshold'
          - 'GreaterThanOrEqualToThreshold'
    threshold:
        description:
          - Sets the min/max bound for triggering the alarm
        required: false
    period:
        description:
          - The time (in seconds) between metric evaluations
        required: false
    evaluation_periods:
        description:
          - The number of times in which the metric is evaluated before final calculation
        required: false
    unit:
        description:
          - The threshold's unit of measurement
        required: false
        choices:
          - 'Seconds'
          - 'Microseconds'
          - 'Milliseconds'
          - 'Bytes'
          - 'Kilobytes'
          - 'Megabytes'
          - 'Gigabytes'
          - 'Terabytes'
          - 'Bits'
          - 'Kilobits'
          - 'Megabits'
          - 'Gigabits'
          - 'Terabits'
          - 'Percent'
          - 'Count'
          - 'Bytes/Second'
          - 'Kilobytes/Second'
          - 'Megabytes/Second'
          - 'Gigabytes/Second'
          - 'Terabytes/Second'
          - 'Bits/Second'
          - 'Kilobits/Second'
          - 'Megabits/Second'
          - 'Gigabits/Second'
          - 'Terabits/Second'
          - 'Count/Second'
          - 'None'
    description:
        description:
          - A longer description of the alarm
        required: false
    dimensions:
        description:
          - Describes to what the alarm is applied
        required: false
    alarm_actions:
        description:
          - A list of the names action(s) taken when the alarm is in the 'alarm' status
        required: false
    insufficient_data_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the 'insufficient_data' status
        required: false
    ok_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the 'ok' status
        required: false
    treat_missing_data:
        description:
          - Sets how the alarm handles missing data points.
        required: false
        choices:
          - 'breaching'
          - 'notBreaching'
          - 'ignore'
          - 'missing'
        default: 'missing'
        version_added: "2.5"
extends_documentation_fragment:
    - aws
    - ec2
"""

EXAMPLES = '''
  - name: create alarm
    ec2_metric_alarm:
      state: present
      region: ap-southeast-2
      name: "cpu-low"
      metric: "CPUUtilization"
      namespace: "AWS/EC2"
      statistic: Average
      comparison: "LessThanOrEqualToThreshold"
      threshold: 5.0
      period: 300
      evaluation_periods: 3
      unit: "Percent"
      description: "This will alarm when a bamboo slave's cpu usage average is lower than 5% for 15 minutes "
      dimensions: {'InstanceId':'i-XXX'}
      alarm_actions: ["action1","action2"]
'''

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, ec2_argument_spec,
                                      get_aws_connection_info)


def compare_dicts(dict_a, dict_b, keys):
    for k in keys:
        if dict_a.get(k) != dict_b.get(k):
            return True
    return False


def create_metric_alarm(connection, module):
    comparisons = {
        '<=': 'LessThanOrEqualToThreshold',
        '<': 'LessThanThreshold',
        '>=': 'GreaterThanOrEqualToThreshold',
        '>': 'GreaterThanThreshold'
    }

    warnings = []
    name = module.params.get('name')
    comparison = module.params.get('comparison')
    if comparison in ('<=', '<', '>', '>='):
        warnings.append('Using the <=, <, > and >= operators for comparison has been deprecated. Please use LessThanOrEqualToThreshold, '
                        'LessThanThreshold, GreaterThanThreshold or GreaterThanOrEqualToThreshold instead.')
        comparison = comparisons[comparison]
    dimensions = module.params.get('dimensions')
    if not isinstance(dimensions, list):
        fixed_dimensions = []
        for key, value in dimensions.items():
            fixed_dimensions.append({'Name': key, 'Value': value})
        dimensions = fixed_dimensions

    module_alarm = dict(
        AlarmName=name,
        MetricName=module.params.get('metric'),
        Namespace=module.params.get('namespace'),
        Statistic=module.params.get('statistic'),
        ComparisonOperator=comparison,
        Threshold=module.params.get('threshold'),
        Period=module.params.get('period'),
        EvaluationPeriods=module.params.get('evaluation_periods'),
        Unit=module.params.get('unit'),
        AlarmDescription=module.params.get('description'),
        Dimensions=dimensions,
        AlarmActions=module.params.get('alarm_actions') or [],
        InsufficientDataActions=module.params.get('insufficient_data_actions') or [],
        OKActions=module.params.get('ok_actions') or [],
        TreatMissingData=module.params.get('treat_missing_data'),
    )
    # botocore expects params values to be set explicitly, it breaks when some of them are NULLs.
    # If the param value is NULL, do not send in the request
    for key, value in module_alarm.items():
        if value is None:
            del module_alarm[key]

    alarms = connection.describe_alarms(AlarmNames=[name])
    if not alarms['MetricAlarms']:  # we create alarm
        try:
            connection.put_metric_alarm(**module_alarm)
            changed = True
            alarms = connection.describe_alarms(AlarmNames=[name])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))

    else:
        cloudwatch_alarm = alarms['MetricAlarms'][0]

        # Workaround for alarms created before TreatMissingData was introduced
        if 'TreatMissingData' not in module_alarm.keys():
            module_alarm['TreatMissingData'] = 'missing'

        changed = compare_dicts(module_alarm, cloudwatch_alarm, [
            'AlarmName', 'MetricName', 'Namespace', 'Statistic',
            'ComparisonOperator', 'Threshold',
            'Period', 'EvaluationPeriods', 'Unit',
            'AlarmDescription', 'Dimensions',
            'AlarmActions', 'InsufficientDataActions', 'OKActions',
            'TreatMissingData'
        ])
        if changed:
            try:
                connection.put_metric_alarm(**module_alarm)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg=str(e))

    result = alarms['MetricAlarms'][0]
    module.exit_json(
        changed=changed,
        warnings=warnings,
        name=result.get('AlarmName'),
        actions_enabled=result.get('ActionsEnabled'),
        alarm_actions=result.get('AlarmActions'),
        alarm_arn=result.get('AlarmArn'),
        comparison=result.get('ComparisonOperator'),
        description=result.get('AlarmDescription'),
        dimensions=result.get('Dimensions'),
        evaluation_periods=result.get('EvaluationPeriods'),
        insufficient_data_actions=result.get('InsufficientDataActions'),
        last_updated=result.get('AlarmConfigurationUpdatedTimestamp'),
        metric=result.get('MetricName'),
        namespace=result.get('Namespace'),
        ok_actions=result.get('OKActions'),
        period=result.get('Period'),
        state_reason=result.get('StateReason'),
        state_value=result.get('StateValue'),
        statistic=result.get('Statistic'),
        threshold=result.get('Threshold'),
        unit=result.get('Unit')
    )


def delete_metric_alarm(connection, module):
    name = module.params.get('name')
    alarms = connection.describe_alarms(AlarmNames=[name])

    if alarms['MetricAlarms']:
        try:
            connection.delete_alarms(AlarmNames=[name])
            module.exit_json(changed=True)
        except (botocore.exceptions.ClientError) as e:
            module.fail_json(msg=str(e))
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            metric=dict(type='str'),
            namespace=dict(type='str'),
            statistic=dict(type='str', choices=['SampleCount', 'Average', 'Sum', 'Minimum', 'Maximum']),
            comparison=dict(type='str', choices=['LessThanOrEqualToThreshold', 'LessThanThreshold', 'GreaterThanThreshold',
                                                 'GreaterThanOrEqualToThreshold', '<=', '<', '>', '>=']),
            threshold=dict(type='float'),
            period=dict(type='int'),
            unit=dict(type='str', choices=['Seconds', 'Microseconds', 'Milliseconds', 'Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes',
                                           'Terabytes', 'Bits', 'Kilobits', 'Megabits', 'Gigabits', 'Terabits', 'Percent', 'Count',
                                           'Bytes/Second', 'Kilobytes/Second', 'Megabytes/Second', 'Gigabytes/Second',
                                           'Terabytes/Second', 'Bits/Second', 'Kilobits/Second', 'Megabits/Second', 'Gigabits/Second',
                                           'Terabits/Second', 'Count/Second', 'None']),
            evaluation_periods=dict(type='int'),
            description=dict(type='str'),
            dimensions=dict(type='dict', default={}),
            alarm_actions=dict(type='list'),
            insufficient_data_actions=dict(type='list'),
            ok_actions=dict(type='list'),
            treat_missing_data=dict(type='str', choices=['breaching', 'notBreaching', 'ignore', 'missing'], default='missing'),
            state=dict(default='present', choices=['present', 'absent']),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    if region:
        try:
            connection = boto3_conn(module, conn_type='client', resource='cloudwatch',
                                    region=region, endpoint=ec2_url, **aws_connect_params)
        except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
            module.fail_json(msg=str(e))
    else:
        module.fail_json(msg="region must be specified")

    if state == 'present':
        create_metric_alarm(connection, module)
    elif state == 'absent':
        delete_metric_alarm(connection, module)


if __name__ == '__main__':
    main()
