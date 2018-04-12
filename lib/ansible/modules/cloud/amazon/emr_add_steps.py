#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: emr_add_steps
short_description: Add a step or a series of steps to an existing EMR Cluster
description:
    - Module adds a step or a series of steps to an existing Amazon EMR cluster
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
    cluster_id:
        description:
            - Cluster ID of the EMR cluster.
        required: true
    steps:
        description:
            - Steps to run against the EMR cluster.
        required: true
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Add steps to be run on specified EMR Cluster
  emr_add_steps:
    cluster_id: j-4FCCDFFHRASSX
    steps:
      - Name: arbitrary_step
        ActionOnFailure: 'CANCEL_AND_WAIT'
        HadoopJarStep:
          Jar: 'command-runner.jar'
          Args: ['-e', 'example-arg']
'''

RETURN = '''
step_ids:
    description: The identifiers of the list of steps added to the job flow.
    returned: success
    type: list
'''


try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def add_emr_steps(conn, module, cluster_id, steps):
    try:
        results = conn.add_job_flow_steps(
            JobFlowId=cluster_id,
            Steps=steps
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't add step(s) to EMR Cluster")
    return camel_dict_to_snake_dict(results)


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'cluster_id': dict(type='str', required=True),
            'steps': dict(type='list', required=True),
        },
        supports_check_mode=True,
    )

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='emr', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    cluster_id = module.params.get('cluster_id')
    steps = module.params.get('steps')

    emr_step_details = add_emr_steps(connection, module, cluster_id, steps)

    module.exit_json(changed=True, ansible_facts={'emr': emr_step_details})


if __name__ == '__main__':
    main()
