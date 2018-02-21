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
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''
---
module: emr_add_steps
short_description: Add a step or a series of steps to an existing EMR Cluster
description:
    - Module adds a step or a series of steps to an existing Amazon EMR cluster
version_added: "2.5"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
    cluster_id:
        description:
            - Cluster ID of the EMR cluster.
        required: true
        default: None
    steps:
        description:
            - Steps to run against the EMR cluster.
        required: true
        default: None
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Add steps to be run on specified EMR Cluster
  emr_add_steps:
    cluster_id: j-4FCCDFFHRASSX
    steps:
      - name: arbitrary_step
        action_on_failure: 'CANCEL_AND_WAIT'
        hadoop_jar_step:
          jar: 'command-runner.jar'
          args: ['-e', 'example-arg']
          properties:
            - key:
              value:
'''

RETURN = '''
step_ids:
    description: The identifiers of the list of steps added to the job flow.
    returned: success
    type: list
'''


from collections import defaultdict

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

import json

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


class EMRConnection(object):

    def __init__(self, module, region, **aws_connect_params):
        try:
            self.connection = boto3_conn(module, conn_type='client',
                                         resource='emr', region=region,
                                         **aws_connect_params)
            self.module = module
        except Exception as e:
            module.fail_json(msg="Failed to connect to AWS: %s" % str(e))

        self.region = region


    def add_emr_steps(self):
        cluster_id = self.module.params.get('cluster_id')
        steps_raw = self.module.params.get('steps')
        steps_json = json.loads(steps_raw)

        try:
            results = self.connection.add_job_flow_steps(
                JobFlowId=cluster_id,
                Steps=steps_json
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            self.module.fail_json_aws(e, msg="Couldn't add step to EMR Cluster")
        return camel_dict_to_snake_dict(results)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        cluster_id=dict(type='string', required=True),
        steps=dict(type='list', required=True)
    ))

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    region, dummy, aws_connect_params = get_aws_connection_info(module, boto3=True)
    connection = EMRConnection(module, region, **aws_connect_params)

    emr_step_details = connection.add_emr_steps()

    module.exit_json(changed=True, ansible_facts={'emr': emr_step_details})


if __name__ == '__main__':
    main()
