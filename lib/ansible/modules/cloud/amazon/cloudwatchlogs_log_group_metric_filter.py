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
module: cloudwatchlogs_log_group_metric_filter
version_added: "2.10"
author:
  - "Markus Bergholz (@markuman)"
short_description: Manage CloudWatch log group metric filter
description:
  - Create, modify and delete CloudWatch log group metric filter.
  - CloudWatch log group metric filter can be use with M(ec2_metric_alarm).
requirements:
  - boto3
  - botocore
options:
    state:
      description:
        - Whether the rule is present or absent.
      choices: ["present", "absent"]
      required: true
      type: str
    log_group_name:
      description:
        - The name of the log group where the metric filter is applied on.
      required: true
      type: str
    filter_name:
      description:
        - A name for the metric filter you create.
      required: true
      type: str
    filter_pattern:
      description:
        - A filter pattern for extracting metric data out of ingested log events. Required when I(state=present).
      type: str
    metric_transformation:
      description:
        - A collection of information that defines how metric data gets emitted. Required when I(state=present).
      type: dict
      suboptions:
        metric_name:
          description:
            - The name of the cloudWatch metric.
          type: str
        metric_namespace:
          description:
            - The namespace of the cloudWatch metric.
          type: str
        metric_value:
          description:
            - The value to publish to the cloudWatch metric when a filter pattern matches a log event.
          type: str
        default_value:
          description:
            - The value to emit when a filter pattern does not match a log event.
          type: float
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- name: set metric filter on log group /fluentd/testcase
  cloudwatchlogs_log_group_metric_filter:
    log_group_name: /fluentd/testcase
    filter_name: BoxFreeStorage
    filter_pattern: '{($.value = *) && ($.hostname = "box")}'
    state: present
    metric_transformation:
        metric_name: box_free_space
        metric_namespace: fluentd_metrics
        metric_value: "$.value"

- name: delete metric filter on log group /fluentd/testcase
  cloudwatchlogs_log_group_metric_filter:
    log_group_name: /fluentd/testcase
    filter_name: BoxFreeStorage
    state: absent
'''

RETURN = """
metric_filters:
    description: Return the origin response value
    returned: success
    type: list
    contains:
        creation_time:
        filter_name:
        filter_pattern:
        log_group_name:
        metric_filter_count:
"""
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters
from ansible.module_utils.ec2 import camel_dict_to_snake_dict

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def metricTransformationHandler(metricTransformations, originMetricTransformations=None):

    if originMetricTransformations:
        change = False
        originMetricTransformations = camel_dict_to_snake_dict(
            originMetricTransformations)
        for item in ["default_value", "metric_name", "metric_namespace", "metric_value"]:
            if metricTransformations.get(item) != originMetricTransformations.get(item):
                change = True
    else:
        change = True

    defaultValue = metricTransformations.get("default_value")
    if isinstance(defaultValue, int) or isinstance(defaultValue, float):
        retval = [
            {
                'metricName': metricTransformations.get("metric_name"),
                'metricNamespace': metricTransformations.get("metric_namespace"),
                'metricValue': metricTransformations.get("metric_value"),
                'defaultValue': defaultValue
            }
        ]
    else:
        retval = [
            {
                'metricName': metricTransformations.get("metric_name"),
                'metricNamespace': metricTransformations.get("metric_namespace"),
                'metricValue': metricTransformations.get("metric_value"),
            }
        ]

    return retval, change


def main():

    arg_spec = dict(
        state=dict(type='str', required=True, choices=['present', 'absent']),
        log_group_name=dict(type='str', required=True),
        filter_name=dict(type='str', required=True),
        filter_pattern=dict(type='str'),
        metric_transformation=dict(type='dict', options=dict(
            metric_name=dict(type='str'),
            metric_namespace=dict(type='str'),
            metric_value=dict(type='str'),
            default_value=dict(type='float')
        )),
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True,
        required_if=[('state', 'present', ['metric_transformation', 'filter_pattern'])]
    )

    log_group_name = module.params.get("log_group_name")
    filter_name = module.params.get("filter_name")
    filter_pattern = module.params.get("filter_pattern")
    metric_transformation = module.params.get("metric_transformation")
    state = module.params.get("state")

    cwl = module.client('logs')

    # check if metric filter exists
    response = cwl.describe_metric_filters(
        logGroupName=log_group_name,
        filterNamePrefix=filter_name
    )

    if len(response.get("metricFilters")) == 1:
        originMetricTransformations = response.get(
            "metricFilters")[0].get("metricTransformations")[0]
        originFilterPattern = response.get("metricFilters")[
            0].get("filterPattern")
    else:
        originMetricTransformations = None
        originFilterPattern = None
    change = False
    metricTransformation = None

    if state == "absent" and originMetricTransformations:
        if not module.check_mode:
            response = cwl.delete_metric_filter(
                logGroupName=log_group_name,
                filterName=filter_name
            )
        change = True
        metricTransformation = [camel_dict_to_snake_dict(item) for item in [originMetricTransformations]]

    elif state == "present":
        metricTransformation, change = metricTransformationHandler(
            metricTransformations=metric_transformation, originMetricTransformations=originMetricTransformations)

        change = change or filter_pattern != originFilterPattern

        if change:
            if not module.check_mode:
                response = cwl.put_metric_filter(
                    logGroupName=log_group_name,
                    filterName=filter_name,
                    filterPattern=filter_pattern,
                    metricTransformations=metricTransformation
                )

        metricTransformation = [camel_dict_to_snake_dict(item) for item in metricTransformation]

    module.exit_json(changed=change, metric_filters=metricTransformation)


if __name__ == '__main__':
    main()
