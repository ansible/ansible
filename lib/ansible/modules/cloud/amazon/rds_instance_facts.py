#!/usr/bin/python
# Copyright (c) 2017, 2018 Michael De La Rue
# Copyright (c) 2017, 2018 Will Thames
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: rds_instance_facts
version_added: "2.6"
short_description: obtain facts about one or more RDS instances
description:
  - obtain facts about one or more RDS instances
options:
  db_instance_identifier:
    description:
      - The RDS instance's unique identifier.
    required: false
    aliases:
      - id
  filters:
    description:
      - A filter that specifies one or more DB instances to describe.
        See U(https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeDBInstances.html)
requirements:
    - "python >= 2.7"
    - "boto3"
author:
    - "Will Thames (@willthames)"
    - "Michael De La Rue (@mikedlr)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Get facts about an instance
- rds_instance_facts:
    db_instance_identifier: new-database
  register: new_database_facts

# Get all RDS instances
- rds_instance_facts:
'''

RETURN = '''
instances:
  description: List of RDS instances
  returned: always
  type: complex
  contains:
    allocated_storage:
      description: Gigabytes of storage allocated to the database
      returned: always
      type: int
      sample: 10
    auto_minor_version_upgrade:
      description: Whether minor version upgrades happen automatically
      returned: always
      type: bool
      sample: true
    availability_zone:
      description: Availability Zone in which the database resides
      returned: always
      type: str
      sample: us-west-2b
    backup_retention_period:
      description: Days for which backups are retained
      returned: always
      type: int
      sample: 7
    ca_certificate_identifier:
      description: ID for the CA certificate
      returned: always
      type: str
      sample: rds-ca-2015
    copy_tags_to_snapshot:
      description: Whether DB tags should be copied to the snapshot
      returned: always
      type: bool
      sample: false
    db_instance_arn:
      description: ARN of the database instance
      returned: always
      type: str
      sample: arn:aws:rds:us-west-2:111111111111:db:helloworld-rds
    db_instance_class:
      description: Instance class of the database instance
      returned: always
      type: str
      sample: db.t2.small
    db_instance_identifier:
      description: Database instance identifier
      returned: always
      type: str
      sample: helloworld-rds
    db_instance_port:
      description: Port used by the database instance
      returned: always
      type: int
      sample: 0
    db_instance_status:
      description: Status of the database instance
      returned: always
      type: str
      sample: available
    db_name:
      description: Name of the database
      returned: always
      type: str
      sample: management
    db_parameter_groups:
      description: List of database parameter groups
      returned: always
      type: complex
      contains:
        db_parameter_group_name:
          description: Name of the database parameter group
          returned: always
          type: str
          sample: psql-pg-helloworld
        parameter_apply_status:
          description: Whether the parameter group has been applied
          returned: always
          type: str
          sample: in-sync
    db_security_groups:
      description: List of security groups used by the database instance
      returned: always
      type: list
      sample: []
    db_subnet_group:
      description: list of subnet groups
      returned: always
      type: complex
      contains:
        db_subnet_group_description:
          description: Description of the DB subnet group
          returned: always
          type: str
          sample: My database subnet group
        db_subnet_group_name:
          description: Name of the database subnet group
          returned: always
          type: str
          sample: my-subnet-group
        subnet_group_status:
          description: Subnet group status
          returned: always
          type: str
          sample: Complete
        subnets:
          description: List of subnets in the subnet group
          returned: always
          type: complex
          contains:
            subnet_availability_zone:
              description: Availability zone of the subnet
              returned: always
              type: complex
              contains:
                name:
                  description: Name of the availability zone
                  returned: always
                  type: str
                  sample: us-west-2c
            subnet_identifier:
              description: Subnet ID
              returned: always
              type: str
              sample: subnet-abcd1234
            subnet_status:
              description: Subnet status
              returned: always
              type: str
              sample: Active
        vpc_id:
          description: VPC id of the subnet group
          returned: always
          type: str
          sample: vpc-abcd1234
    dbi_resource_id:
      description: AWS Region-unique, immutable identifier for the DB instance
      returned: always
      type: str
      sample: db-AAAAAAAAAAAAAAAAAAAAAAAAAA
    domain_memberships:
      description: List of domain memberships
      returned: always
      type: list
      sample: []
    endpoint:
      description: Database endpoint
      returned: always
      type: complex
      contains:
        address:
          description: Database endpoint address
          returned: always
          type: str
          sample: helloworld-rds.ctrqpe3so1sf.us-west-2.rds.amazonaws.com
        hosted_zone_id:
          description: Route53 hosted zone ID
          returned: always
          type: str
          sample: Z1PABCD0000000
        port:
          description: Database endpoint port
          returned: always
          type: int
          sample: 5432
    engine:
      description: Database engine
      returned: always
      type: str
      sample: postgres
    engine_version:
      description: Database engine version
      returned: always
      type: str
      sample: 9.5.10
    iam_database_authentication_enabled:
      description: Whether database authentication through IAM is enabled
      returned: always
      type: bool
      sample: false
    instance_create_time:
      description: Date and time the instance was created
      returned: always
      type: str
      sample: '2017-10-10T04:00:07.434000+00:00'
    kms_key_id:
      description: KMS Key ID
      returned: always
      type: str
      sample: arn:aws:kms:us-west-2:111111111111:key/abcd1234-0000-abcd-1111-0123456789ab
    latest_restorable_time:
      description: Latest time to which a database can be restored with point-in-time restore
      returned: always
      type: str
      sample: '2018-05-17T00:03:56+00:00'
    license_model:
      description: License model
      returned: always
      type: str
      sample: postgresql-license
    master_username:
      description: Database master username
      returned: always
      type: str
      sample: dbadmin
    monitoring_interval:
      description: Interval, in seconds, between points when Enhanced Monitoring metrics are collected for the DB instance
      returned: always
      type: int
      sample: 0
    multi_az:
      description: Whether Multi-AZ is on
      returned: always
      type: bool
      sample: false
    option_group_memberships:
      description: List of option groups
      returned: always
      type: complex
      contains:
        option_group_name:
          description: Option group name
          returned: always
          type: str
          sample: default:postgres-9-5
        status:
          description: Status of option group
          returned: always
          type: str
          sample: in-sync
    pending_modified_values:
      description: Modified values pending application
      returned: always
      type: complex
      contains: {}
    performance_insights_enabled:
      description: Whether performance insights are enabled
      returned: always
      type: bool
      sample: false
    preferred_backup_window:
      description: Preferred backup window
      returned: always
      type: str
      sample: 04:00-05:00
    preferred_maintenance_window:
      description: Preferred maintenance window
      returned: always
      type: str
      sample: mon:05:00-mon:05:30
    publicly_accessible:
      description: Whether the DB is publicly accessible
      returned: always
      type: bool
      sample: false
    read_replica_db_instance_identifiers:
      description: List of database instance read replicas
      returned: always
      type: list
      sample: []
    storage_encrypted:
      description: Whether the storage is encrypted
      returned: always
      type: bool
      sample: true
    storage_type:
      description: Storage type of the Database instance
      returned: always
      type: str
      sample: gp2
    tags:
      description: Tags used by the database instance
      returned: always
      type: complex
      contains: {}
    vpc_security_groups:
      description: List of VPC security groups
      returned: always
      type: complex
      contains:
        status:
          description: Status of the VPC security group
          returned: always
          type: str
          sample: active
        vpc_security_group_id:
          description: VPC Security Group ID
          returned: always
          type: str
          sample: sg-abcd1234
'''

from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, boto3_tag_list_to_ansible_dict, AWSRetry, camel_dict_to_snake_dict


try:
    import botocore
except ImportError:
    pass  # handled by AnsibleAWSModule


def instance_facts(module, conn):
    instance_name = module.params.get('db_instance_identifier')
    filters = module.params.get('filters')

    params = dict()
    if instance_name:
        params['DBInstanceIdentifier'] = instance_name
    if filters:
        params['Filters'] = ansible_dict_to_boto3_filter_list(filters)

    paginator = conn.get_paginator('describe_db_instances')
    try:
        results = paginator.paginate(**params).build_full_result()['DBInstances']
    except is_boto3_error_code('DBInstanceNotFound'):
        results = []
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:  # pylint: disable=duplicate-except
        module.fail_json_aws(e, "Couldn't get instance information")

    for instance in results:
        try:
            instance['Tags'] = boto3_tag_list_to_ansible_dict(conn.list_tags_for_resource(ResourceName=instance['DBInstanceArn'],
                                                                                          aws_retry=True)['TagList'])
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, "Couldn't get tags for instance %s" % instance['DBInstanceIdentifier'])

    return dict(changed=False, instances=[camel_dict_to_snake_dict(instance, ignore_list=['Tags']) for instance in results])


def main():
    argument_spec = dict(
        db_instance_identifier=dict(aliases=['id']),
        filters=dict(type='dict')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    conn = module.client('rds', retry_decorator=AWSRetry.jittered_backoff(retries=10))

    module.exit_json(**instance_facts(module, conn))


if __name__ == '__main__':
    main()
