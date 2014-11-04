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

DOCUMENTATION = """
module: ec2_metric_alarm
short_description: "Create/update or delete AWS Cloudwatch 'metric alarms'"
description:
 - Can create or delete AWS metric alarms
 - Metrics you wish to alarm on must already exist
version_added: "1.6"
author: Zacharie Eakin
options:
    state:
        description:
          - register or deregister the alarm
        required: true
        choices: ['present', 'absent']
    name:
        desciption:
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
        options: ['SampleCount','Average','Sum','Minimum','Maximum']
    comparison:
        description:
          - Determines how the threshold value is compared
        required: false
        options: ['<=','<','>','>=']
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
        options: ['Seconds','Microseconds','Milliseconds','Bytes','Kilobytes','Megabytes','Gigabytes','Terabytes','Bits','Kilobits','Megabits','Gigabits','Terabits','Percent','Count','Bytes/Second','Kilobytes/Second','Megabytes/Second','Gigabytes/Second','Terabytes/Second','Bits/Second','Kilobits/Second','Megabits/Second','Gigabits/Second','Terabits/Second','Count/Second','None']
    description:
        description:
          - A longer desciption of the alarm
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
extends_documentation_fragment: aws
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
      comparison: "<="
      threshold: 5.0
      period: 300
      evaluation_periods: 3
      unit: "Percent"
      description: "This will alarm when a bamboo slave's cpu usage average is lower than 5% for 15 minutes "
      dimensions: {'InstanceId':'i-XXX'}
      alarm_actions: ["action1","action2"]


'''

import sys

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto.ec2.cloudwatch
    from boto.ec2.cloudwatch import CloudWatchConnection, MetricAlarm
    from boto.exception import BotoServerError
except ImportError:
    print "failed=True msg='boto required for this module'"
    sys.exit(1)


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

    alarms = connection.describe_alarms(alarm_names=[name])

    if not alarms:

        alm = MetricAlarm(
            name=name,
            metric=metric,
            namespace=namespace,
            statistic=statistic,
            comparison=comparison,
            threshold=threshold,
            period=period,
            evaluation_periods=evaluation_periods,
            unit=unit,
            description=description,
            dimensions=dimensions,
            alarm_actions=alarm_actions,
            insufficient_data_actions=insufficient_data_actions,
            ok_actions=ok_actions
        )
        try:
            connection.create_alarm(alm)
            changed = True
            alarms = connection.describe_alarms(alarm_names=[name])
        except BotoServerError, e:
            module.fail_json(msg=str(e))

    else:
        alarm = alarms[0]
        changed = False

        for attr in ('comparison','metric','namespace','statistic','threshold','period','evaluation_periods','unit','description'):
            if getattr(alarm, attr) != module.params.get(attr):
                changed = True
                setattr(alarm, attr, module.params.get(attr))
        #this is to deal with a current bug where you cannot assign '<=>' to the comparator when modifying an existing alarm
        comparison = alarm.comparison
        comparisons = {'<=' : 'LessThanOrEqualToThreshold', '<' : 'LessThanThreshold', '>=' : 'GreaterThanOrEqualToThreshold', '>' : 'GreaterThanThreshold'}
        alarm.comparison = comparisons[comparison]

        dim1 = module.params.get('dimensions')
        dim2 = alarm.dimensions

        for keys in dim1:
            if not isinstance(dim1[keys], list):
                dim1[keys] = [dim1[keys]]
            if dim1[keys] != dim2[keys]:
                changed=True
                setattr(alarm, 'dimensions', dim1)

        for attr in ('alarm_actions','insufficient_data_actions','ok_actions'):
            action = module.params.get(attr) or []
            if getattr(alarm, attr) != action:
                changed = True
                setattr(alarm, attr, module.params.get(attr))

        try:
            if changed:
                connection.create_alarm(alarm)
        except BotoServerError, e:
            module.fail_json(msg=str(e))
    result = alarms[0]
    module.exit_json(changed=changed, name=result.name,
        actions_enabled=result.actions_enabled,
        alarm_actions=result.alarm_actions,
        alarm_arn=result.alarm_arn,
        comparison=result.comparison,
        description=result.description,
        dimensions=result.dimensions,
        evaluation_periods=result.evaluation_periods,
        insufficient_data_actions=result.insufficient_data_actions,
        last_updated=result.last_updated,
        metric=result.metric,
        namespace=result.namespace,
        ok_actions=result.ok_actions,
        period=result.period,
        state_reason=result.state_reason,
        state_value=result.state_value,
        statistic=result.statistic,
        threshold=result.threshold,
        unit=result.unit)

def delete_metric_alarm(connection, module):
    name = module.params.get('name')

    alarms = connection.describe_alarms(alarm_names=[name])

    if alarms:
        try:
            connection.delete_alarms([name])
            module.exit_json(changed=True)
        except BotoServerError, e:
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
            comparison=dict(type='str', choices=['<=', '<', '>', '>=']),
            threshold=dict(type='float'),
            period=dict(type='int'),
            unit=dict(type='str', choices=['Seconds', 'Microseconds', 'Milliseconds', 'Bytes', 'Kilobytes', 'Megabytes', 'Gigabytes', 'Terabytes', 'Bits', 'Kilobits', 'Megabits', 'Gigabits', 'Terabits', 'Percent', 'Count', 'Bytes/Second', 'Kilobytes/Second', 'Megabytes/Second', 'Gigabytes/Second', 'Terabytes/Second', 'Bits/Second', 'Kilobits/Second', 'Megabits/Second', 'Gigabits/Second', 'Terabits/Second', 'Count/Second', 'None']),
            evaluation_periods=dict(type='int'),
            description=dict(type='str'),
            dimensions=dict(type='dict'),
            alarm_actions=dict(type='list'),
            insufficient_data_actions=dict(type='list'),
            ok_actions=dict(type='list'),
            state=dict(default='present', choices=['present', 'absent']),
            region=dict(aliases=['aws_region', 'ec2_region'], choices=AWS_REGIONS),
           )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    state = module.params.get('state')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module)
    try:
        connection = connect_to_aws(boto.ec2.cloudwatch, region, **aws_connect_params)
    except boto.exception.NoAuthHandlerFound, e:
        module.fail_json(msg=str(e))

    if state == 'present':
        create_metric_alarm(connection, module)
    elif state == 'absent':
        delete_metric_alarm(connection, module)

main()
