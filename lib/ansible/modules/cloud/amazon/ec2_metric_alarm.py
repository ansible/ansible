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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: ec2_metric_alarm
short_description: "Create/update or delete AWS Cloudwatch 'metric alarms'"
description:
 - Can create or delete AWS metric alarms.
 - Metrics you wish to alarm on must already exist.
version_added: "1.6"
author: "Zacharie Eakin (@Zeekin)"
options:
    state:
        description:
          - Register or deregister the alarm.
        choices: ['present', 'absent']
        default: 'present'
        type: str
    name:
        description:
          - Unique name for the alarm.
        required: true
        type: str
    metric:
        description:
          - Name of the monitored metric (e.g. C(CPUUtilization)).
          - Metric must already exist.
        required: false
        type: str
    namespace:
        description:
          - Name of the appropriate namespace (C(AWS/EC2), C(System/Linux), etc.), which determines the category it will appear under in cloudwatch.
        required: false
        type: str
    statistic:
        description:
          - Operation applied to the metric.
          - Works in conjunction with I(period) and I(evaluation_periods) to determine the comparison value.
        required: false
        choices: ['SampleCount','Average','Sum','Minimum','Maximum']
        type: str
    comparison:
        description:
          - Determines how the threshold value is compared
          - Symbolic comparison operators have been deprecated, and will be removed in 2.14
        required: false
        type: str
        choices:
          - 'GreaterThanOrEqualToThreshold'
          - 'GreaterThanThreshold'
          - 'LessThanThreshold'
          - 'LessThanOrEqualToThreshold'
          - '<='
          - '<'
          - '>='
          - '>'
    threshold:
        description:
          - Sets the min/max bound for triggering the alarm.
        required: false
        type: float
    period:
        description:
          - The time (in seconds) between metric evaluations.
        required: false
        type: int
    evaluation_periods:
        description:
          - The number of times in which the metric is evaluated before final calculation.
        required: false
        type: int
    unit:
        description:
          - The threshold's unit of measurement.
        required: false
        type: str
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
          - A longer description of the alarm.
        required: false
        type: str
    dimensions:
        description:
          - A dictionary describing which metric the alarm is applied to.
          - 'For more information see the AWS documentation:'
          - U(https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#Dimension)
        required: false
        type: dict
    alarm_actions:
        description:
          - A list of the names action(s) taken when the alarm is in the C(alarm) status, denoted as Amazon Resource Name(s).
        required: false
        type: list
        elements: str
    insufficient_data_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the C(insufficient_data) status.
        required: false
        type: list
        elements: str
    ok_actions:
        description:
          - A list of the names of action(s) to take when the alarm is in the C(ok) status, denoted as Amazon Resource Name(s).
        required: false
        type: list
        elements: str
    treat_missing_data:
        description:
          - Sets how the alarm handles missing data points.
        required: false
        type: str
        choices:
          - 'breaching'
          - 'notBreaching'
          - 'ignore'
          - 'missing'
        default: 'missing'
        version_added: "2.10"
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

  - name: Create an alarm to recover a failed instance
    ec2_metric_alarm:
      state: present
      region: us-west-1
      name: "recover-instance"
      metric: "StatusCheckFailed_System"
      namespace: "AWS/EC2"
      statistic: "Minimum"
      comparison: ">="
      threshold: 1.0
      period: 60
      evaluation_periods: 2
      unit: "Count"
      description: "This will recover an instance when it fails"
      dimensions: {"InstanceId":'i-XXX'}
      alarm_actions: ["arn:aws:automate:us-west-1:ec2:recover"]

'''

from ansible.module_utils.aws.core import AnsibleAWSModule

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # protected by AnsibleAWSModule


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

    comparisons = {'<=': 'LessThanOrEqualToThreshold',
                   '<': 'LessThanThreshold',
                   '>=': 'GreaterThanOrEqualToThreshold',
                   '>': 'GreaterThanThreshold'}
    if comparison in ('<=', '<', '>', '>='):
        module.deprecate('Using the <=, <, > and >= operators for comparison has been deprecated. Please use LessThanOrEqualToThreshold, '
                         'LessThanThreshold, GreaterThanThreshold or GreaterThanOrEqualToThreshold instead.', version="2.14")
        comparison = comparisons[comparison]

    if not isinstance(dimensions, list):
        fixed_dimensions = []
        for key, value in dimensions.items():
            fixed_dimensions.append({'Name': key, 'Value': value})
        dimensions = fixed_dimensions

    if not alarms['MetricAlarms']:
        try:
            connection.put_metric_alarm(AlarmName=name,
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
                                        TreatMissingData=treat_missing_data)
            changed = True
            alarms = connection.describe_alarms(AlarmNames=[name])
        except ClientError as e:
            module.fail_json_aws(e)

    else:
        changed = False
        alarm = alarms['MetricAlarms'][0]

        # Workaround for alarms created before TreatMissingData was introduced
        if 'TreatMissingData' not in alarm.keys():
            alarm['TreatMissingData'] = 'missing'

        for key, value in {'MetricName': metric,
                           'Namespace': namespace,
                           'Statistic': statistic,
                           'ComparisonOperator': comparison,
                           'Threshold': threshold,
                           'Period': period,
                           'EvaluationPeriods': evaluation_periods,
                           'Unit': unit,
                           'AlarmDescription': description,
                           'Dimensions': dimensions,
                           'TreatMissingData': treat_missing_data}.items():
            try:
                if alarm[key] != value:
                    changed = True
            except KeyError:
                if value is not None:
                    changed = True

            alarm[key] = value

        for key, value in {'AlarmActions': alarm_actions,
                           'InsufficientDataActions': insufficient_data_actions,
                           'OKActions': ok_actions}.items():
            action = value or []
            if alarm[key] != action:
                changed = True
                alarm[key] = value

        try:
            if changed:
                connection.put_metric_alarm(AlarmName=alarm['AlarmName'],
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
                                            TreatMissingData=alarm['TreatMissingData'])
        except ClientError as e:
            module.fail_json_aws(e)

    result = alarms['MetricAlarms'][0]
    module.exit_json(changed=changed, warnings=warnings,
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
                     treat_missing_data=result['TreatMissingData'],
                     unit=result['Unit'])


def delete_metric_alarm(connection, module):
    name = module.params.get('name')
    alarms = connection.describe_alarms(AlarmNames=[name])

    if alarms['MetricAlarms']:
        try:
            connection.delete_alarms(AlarmNames=[name])
            module.exit_json(changed=True)
        except (ClientError) as e:
            module.fail_json_aws(e)
    else:
        module.exit_json(changed=False)


def main():
    argument_spec = dict(
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
        alarm_actions=dict(type='list', default=[]),
        insufficient_data_actions=dict(type='list', default=[]),
        ok_actions=dict(type='list', default=[]),
        treat_missing_data=dict(type='str', choices=['breaching', 'notBreaching', 'ignore', 'missing'], default='missing'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec)

    state = module.params.get('state')

    connection = module.client('cloudwatch')

    if state == 'present':
        create_metric_alarm(connection, module)
    elif state == 'absent':
        delete_metric_alarm(connection, module)


if __name__ == '__main__':
    main()
