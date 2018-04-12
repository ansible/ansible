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
module: emr_cluster_facts
short_description: Get information about an Amazon EMR cluster
description:
    - Module gets information about an Amazon EMR cluster
version_added: "2.6"
requirements: [ boto3 ]
author:
    - "Aaron Smith (@slapula)"
options:
    cluster_id:
        description:
            - ID of the EMR cluster.
        required: true
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
- name: Get EMR Cluster facts from myTestEmrCluster
  emr_cluster_facts:
    cluster_id: 'j-7OV2AF536ZBF'
  register: result
'''

RETURN = '''
cluster:
    description: Dictionary of facts representing properties of an EMR cluster.
    returned: changed
    type: complex
    contains:
        id:
          description: The unique identifier for the cluster
          returned: always
          type: string
          sample: 'j-7OV2AF536ZBF'
        name:
          description: The name of the cluster
          returned: always
          type: string
          sample: 'myTestEmrCluster'
        status:
          description: The current status details about the cluster
          returned: always
          type: dict
          contains:
            state:
              description: The current state of the cluster
              returned: always
              type: string
              sample: 'TERMINATED'
            state_change_reason:
              description: The reason for the cluster status change
              returned: always
              type: dict
              contains:
                code:
                  description: The programmatic code for the state change reason
                  returned: always
                  type: string
                  sample: 'ALL_STEPS_COMPLETED'
                message:
                  description: The descriptive message for the state change reason
                  returned: always
                  type: string
                  sample: 'Steps completed'
            timeline:
              description: A timeline that represents the status of a cluster over the lifetime of the cluster
              returned: always
              type: dict
              contains:
                creaton_date_time:
                  description: The creation date and time of the cluster
                  returned: always
                  type: string
                  sample: '2017-12-07T05:52:13.299000-06:00'
                ready_date_time:
                  description: The date and time when the cluster was ready to execute steps
                  returned: always
                  type: string
                  sample: '2017-12-07T05:56:55.100000-06:00'
                end_date_time:
                  description: The date and time when the cluster was terminated
                  returned: always
                  type: string
                  sample: '2017-12-07T06:05:00.376000-06:00'
        ec2_instance_attributes:
          description: Provides information about the EC2 instances in a cluster grouped by category
          returned: always
          type: dict
          contains:
            ec2_key_name:
              description: The name of the Amazon EC2 key pair to use when connecting with SSH into the master node as a user named "hadoop"
              returned: always
              type: string
              sample: 'hadoop_user'
            ec2_subnet_id:
              description: The id of the Amazon VPC subnet used with the cluster
              returned: always
              type: string
              sample: 'subnet-98bd238e'
            requested_ec2_subnet_ids:
              description: The ids of the Amazon VPC subnets used with an instance fleet
              returned: always
              type: list
              sample: ['subnet-98bd238e']
            ec2_availability_zone:
              description: The Availability Zone in which the cluster will run
              returned: always
              type: string
              sample: 'us-west-1a'
            requested_ec2_availability_zones:
              description: The availability zones used with an instance fleet
              returned: always
              type: list
              sample: ['us-east-1c']
            iam_instance_profile:
              description: The IAM role that was specified when the cluster was launched
              returned: always
              type: string
              sample: 'superuser'
            emr_managed_master_security_group:
              description: The identifier of the Amazon EC2 security group for the master node
              returned: always
              type: string
              sample: 'sg-a7bc966g'
            emr_managed_slave_security_group:
              description: The identifier of the Amazon EC2 security group for the slave nodes
              returned: always
              type: string
              sample: 'sg-5cc9265d'
            service_access_security_group:
              description: The identifier of the Amazon EC2 security group for the Amazon EMR service to access clusters in VPC private subnets
              returned: always
              type: string
              sample: 'sg-5cc9265d'
            additional_master_security_groups:
              description: A list of additional Amazon EC2 security group IDs for the master node
              returned: always
              type: string
              sample: 'sg-5cc9265d'
            additional_slave_security_groups:
              description: A list of additional Amazon EC2 security group IDs for the slave nodes
              returned: always
              type: string
              sample: 'sg-5cc9265d'
        instance_collection_type:
          description: The instance group configuration of the cluster
          returned: always
          type: string
          sample: 'INSTANCE_GROUP'
        log_uri:
          description: The path to the Amazon S3 location where logs for this cluster are stored
          returned: always
          type: string
          sample: 's3n://rando-bucket/tmp/7346763/66338210/logs/'
        requested_ami_version:
          description: The AMI version requested for this cluster
          returned: always
          type: string
          sample: '2.3.6'
        running_ami_version:
          description: The AMI version running on this cluster
          returned: always
          type: string
          sample: '2.3.6'
        release_label:
          description: The release label for the Amazon EMR release
          returned: always
          type: string
        auto_terminate:
          description: Specifies whether the cluster should terminate after completing all steps
          returned: always
          type: bool
          sample: 'true'
        termination_protected:
          description: Indicates whether Amazon EMR will lock the cluster to prevent the EC2 instances from being terminated
          returned: always
          type: bool
          sample: 'true'
        visible_to_all_users:
          description: Indicates whether the cluster is visible to all IAM users of the AWS account associated with the cluster
          returned: always
          type: bool
          sample: 'true'
        applications:
          description: The applications installed on this cluster
          returned: always
          type: list
          sample: [{"name": "hadoop", "version": "1.0.3"}]
        tags:
          description: A list of tags associated with a cluster
          returned: always
          type: list
          sample: [{"key": "name", "value": "myAwesomeCluster"}]
        service_role:
          description: The IAM role that will be assumed by the Amazon EMR service to access AWS resources on your behalf
          returned: always
          type: string
          sample: 'EMR_DefaultRole'
        normalized_instance_hours:
          description: An approximation of the cost of the cluster, represented in m1.small/hours
          returned: always
          type: integer
          sample: 82
        master_public_dns_name:
          description: The DNS name of the master node
          returned: always
          type: string
          sample: 'ec2-54-230-115-229.compute-1.amazonaws.com'
        configurations:
          description: The list of Configurations supplied to the EMR cluster
          returned: always
          type: list
          sample: []
        security_configuration:
          description: The name of the security configuration applied to the cluster
          returned: always
          type: string
          sample: ''
        auto_scaling_role:
          description: An IAM role for automatic scaling policies
          returned: always
          type: string
          sample: 'AwesomeScalingRole'
        scale_down_behavior:
          description: The way that individual Amazon EC2 instances terminate when an automatic scale-in activity occurs
          returned: always
          type: string
          sample: 'TERMINATE_AT_TASK_COMPLETION'
        custom_ami_id:
          description: The ID of a custom Amazon EBS-backed Linux AMI
          returned: always
          type: string
          sample: 'ami-1234567'
        ebs_root_volume_size:
          description: The size, in GiB, of the EBS root device volume of the Linux AMI that is used for each EC2 instance
          returned: always
          type: integer
          sample: 25
        repo_upgrade_on_boot:
          description: Specifies the type of updates that are applied from the Amazon Linux AMI package repositories
          returned: always
          type: string
          sample: ''
'''

try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict


def get_emr_cluster(conn, module, cluster_id):
    try:
        results = conn.describe_cluster(ClusterId=cluster_id)
        results['Cluster']['Tags'] = boto3_tag_list_to_ansible_dict(results['Cluster'].get('Tags', []))
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't get EMR cluster facts")
    return camel_dict_to_snake_dict(results)


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'cluster_id': dict(type='str', required=True),
        },
        supports_check_mode=True,
    )

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    connection = boto3_conn(module, conn_type='client', resource='emr', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    cluster_id = module.params.get('cluster_id')

    emr_cluster_info = get_emr_cluster(connection, module, cluster_id)

    module.exit_json(changed=False, ansible_facts={'EMR': emr_cluster_info})


if __name__ == '__main__':
    main()
