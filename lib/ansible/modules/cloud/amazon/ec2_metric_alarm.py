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


def create_metric_alarm(connection, module):
    name = module.params.get('name')
    metric = module.params.get('metric')
    namespace = module.params.get('namespace')
    statistic = module.params.get('statistic')
    comparison = module.params.get('comparison')
    threshold = module.params.get('threshold')
    period = module.params.get('period')
    evaluation_periods = module.params.get('evaluation_periods')
    unit = module.params.get('unit')
    description = module.params.get('description')
    dimensions = module.params.get('dimensions')
    alarm_actions = module.params.get('alarm_actions')
    insufficient_data_actions = module.params.get('insufficient_data_actions')
    ok_actions = module.params.get('ok_actions')
    treat_missing_data = module.params.get('treat_missing_data')

    warnings = []

    alarms = connection.describe_alarms(AlarmNames=[name])

    comparisons = {
        '<=': 'LessThanOrEqualToThreshold',
        '<': 'LessThanThreshold',
        '>=': 'GreaterThanOrEqualToThreshold',
        '>': 'GreaterThanThreshold'
    }
    if comparison in ('<=', '<', '>', '>='):
        warnings.append('Using the <=, <, > and >= operators for comparison has been deprecated. Please use LessThanOrEqualToThreshold, '
                        'LessThanThreshold, GreaterThanThreshold or GreaterThanOrEqualToThreshold instead.')
        comparison = comparisons[comparison]

    if not isinstance(dimensions, list):
        fixed_dimensions = []
        for key, value in dimensions.items():
            fixed_dimensions.append({'Name': key, 'Value': value})
        dimensions = fixed_dimensions

    if not alarms['MetricAlarms']:  # we create alarm
        try:
            connection.put_metric_alarm(
                AlarmName=name,
                MetricName=metric,
                Namespace=namespace,
                Statistic=statistic,
                ComparisonOperator=comparison,
                Threshold=threshold,
                Period=period,
                EvaluationPeriods=evaluation_periods,
                Unit=unit,
                AlarmDescription=description,
                Dimensions=dimensions,
                AlarmActions=alarm_actions,
                InsufficientDataActions=insufficient_data_actions,
                OKActions=ok_actions,
                TreatMissingData=treat_missing_data
            )
            changed = True
            alarms = connection.describe_alarms(AlarmNames=[name])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))

    else:
        changed = False
        alarm = alarms['MetricAlarms'][0]

        # Workaround for alarms created before TreatMissingData was introduced
        if 'TreatMissingData' not in alarm.keys():
            alarm['TreatMissingData'] = 'missing'

        for key, value in {
            'MetricName': metric,
            'Namespace': namespace,
            'Statistic': statistic,
            'ComparisonOperator': comparison,
            'Threshold': threshold,
            'Period': period,
            'EvaluationPeriods': evaluation_periods,
            'Unit': unit,
            'AlarmDescription': description,
            'Dimensions': dimensions,
            'TreatMissingData': treat_missing_data
        }.items():
            try:
                if alarm[key] != value:
                    changed = True
            except KeyError:
                if value is not None:
                    changed = True

            alarm[key] = value

        for key, value in {
            'AlarmActions': alarm_actions,
            'InsufficientDataActions': insufficient_data_actions,
            'OKActions': ok_actions
        }.items():
            action = value or []
            if alarm[key] != action:
                changed = True
                alarm[key] = value

        try:
            if changed:
                connection.put_metric_alarm(
                    AlarmName=alarm['AlarmName'],
                    MetricName=alarm['MetricName'],
                    Namespace=alarm['Namespace'],
                    Statistic=alarm['Statistic'],
                    ComparisonOperator=alarm['ComparisonOperator'],
                    Threshold=alarm['Threshold'],
                    Period=alarm['Period'],
                    EvaluationPeriods=alarm['EvaluationPeriods'],
                    Unit=alarm['Unit'],
                    AlarmDescription=alarm['AlarmDescription'],
                    Dimensions=alarm['Dimensions'],
                    AlarmActions=alarm['AlarmActions'],
                    InsufficientDataActions=alarm['InsufficientDataActions'],
                    OKActions=alarm['OKActions'],
                    TreatMissingData=alarm['TreatMissingData']
                )
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))

    result = alarms['MetricAlarms'][0]
    module.exit_json(
        changed=changed,
        warnings=warnings,
        name=result['AlarmName'],
        actions_enabled=result['ActionsEnabled'],
        alarm_actions=result['AlarmActions'],
        alarm_arn=result['AlarmArn'],
        comparison=result['ComparisonOperator'],
        description=result['AlarmDescription'],
        dimensions=result['Dimensions'],
        evaluation_periods=result['EvaluationPeriods'],
        insufficient_data_actions=result['InsufficientDataActions'],
        last_updated=result['AlarmConfigurationUpdatedTimestamp'],
        metric=result['MetricName'],
        namespace=result['Namespace'],
        ok_actions=result['OKActions'],
        period=result['Period'],
        state_reason=result['StateReason'],
        state_value=result['StateValue'],
        statistic=result['Statistic'],
        threshold=result['Threshold'],
        unit=result['Unit'])


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
