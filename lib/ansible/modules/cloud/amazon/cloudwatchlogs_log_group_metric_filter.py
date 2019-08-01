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
version_added: "2.9"
short_description: Manage CloudWatch log group metric filter
description:
    - Create, modify and delete Cloudwatch log group metric filter.
    - Cloudwatch log group metric filter can be use with I(ec2_metric_alarm).
requirements:
    - boto3
    - botocore
extends_documentation_fragment:
    - aws
author:
    Markus Bergholz (@markuman)
options:
    log_group_name:
        description:
            - The name of the log group where the metric filter is applied on.
        filter_name:
            - A name for the metric filter you create.
        filter_patten:
            - A filter pattern for extracting metric data out of ingested log events.
        metric_transformation:
            - A collection of information that defines how metric data gets emitted.
            suboptions:
                metricName:
                metricNamespace:
                matricValue:
                defaultValue:

'''

EXAMPLES = '''
- name: set metric filter on log group /fluentd/testcase
    lekker_cloudwatch_metric_filter:
    log_group_name: /fluentd/testcase
    filter_name: BoxFreeStorage
    filter_pattern: '{ ($.value = *) && ($.hostname = "box")}'
    state: present
    metric_transformation:
        metricName: box_free_space
        metricNamespace: fluentd_metrics
        metricValue: "$.value"

- name: delete metric filter on log group /fluentd/testcase
    lekker_cloudwatch_metric_filter:
    log_group_name: /fluentd/testcase
    filter_name: BoxFreeStorage
    state: absent
'''

RETURN = """
logs:
    description: Return the origin response value
    returned: success
    type: list
    contains:
        creationTime:
        filterName:
        filterPattern:
        logGroupName:
        metricTransformation:
"""
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code, get_boto3_client_method_parameters

try:
    from botocore.exceptions import ClientError, BotoCoreError, WaiterError
except ImportError:
    pass  # caught by AnsibleAWSModule


def metricTransformationHandler(metricTransformations, originMetricTransformations=None):

    if originMetricTransformations:
        change = False
        for item in ["defaultValue", "metricName", "metricNamespace", "metricValue"]:
            if metricTransformations.get(item) != originMetricTransformations.get(item):
                change = True
    else:
        change = True

    if metricTransformations.get("defaultValue"):
        retval = [
            {
                'metricName': metricTransformations.get("metricName"),
                'metricNamespace': metricTransformations.get("metricNamespace"),
                'metricValue': metricTransformations.get("metricValue"),
                'defaultValue': metricTransformations.get("defaultValue")
            }
        ]
    else:
        retval = [
            {
                'metricName': metricTransformations.get("metricName"),
                'metricNamespace': metricTransformations.get("metricNamespace"),
                'metricValue': metricTransformations.get("metricValue"),
            }
        ]

    return retval, change


def main():

    arg_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        log_group_name=dict(type='str', required=True),
        filter_name=dict(type='str', required=True),
        filter_pattern=dict(type='str'),
        metric_transformation=dict(
            type='dict', default=dict()),
    )

    module = AnsibleAWSModule(
        argument_spec=arg_spec,
        supports_check_mode=True
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

    if state == "absent" and originMetricTransformations:
        if not module.check_mode:
            response = cwl.delete_metric_filter(
                logGroupName=log_group_name,
                filterName=filter_name
            )
        change = True

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

    module.exit_json(changed=change, logs=response.get("metricFilters"))


if __name__ == '__main__':
    main()
