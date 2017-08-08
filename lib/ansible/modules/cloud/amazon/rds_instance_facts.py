#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: rds_instance_facts
version_added: "2.4"
short_description: obtain facts about one or more RDS instances
description:
  - obtain facts about one or more RDS instances
options:
  name:
    description:
      - Name of an RDS instance.
    required: false
    aliases:
      - name
  filters:
    description:
      - A filter that specifies one or more DB instances to describe.
        See U(https://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeDBInstances.html)
requirements:
    - "python >= 2.6"
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
    name: new-database
  register: new_database_facts

# Get all RDS instances
- rds_instance_facts:
'''

RETURN = '''
instances:
    description: zero or more instances that match the (optional) parameters
    type: list
    returned: always
    sample:
       "instances": [
           {
               "availability_zone": "ap-southeast-2c",
               "backup_retention": 10,
               "create_time": "2017-02-20T06:13:05.724000+00:00",
               "db_engine": "postgres",
               "endpoint": "helloworld-rds-master.cyaju3p4tyqv.ap-southeast-2.rds.amazonaws.com",
               "id": "helloworld-rds-master",
               "instance_type": "db.t2.micro",
               "maintenance_window": "sun:15:40-sun:16:10",
               "multi_zone": false,
               "port": 5432,
               "replication_source": null,
               "size": 5,
               "status": "available",
               "username": "hello",
               "vpc_security_groups": "sg-abcd1234"
           },
       ]
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, ansible_dict_to_boto3_filter_list
from ansible.module_utils.ec2 import boto3_tag_list_to_ansible_dict
from ansible.module_utils.aws.rds import RDSDBInstance

try:
    import botocore
except BaseException:
    pass  # caught by imported HAS_BOTO3


def instance_facts(module, conn):
    instance_name = module.params.get('name')
    filters = module.params.get('filters')

    params = dict()
    if instance_name:
        params['DBInstanceIdentifier'] = instance_name
    if filters:
        params['Filters'] = ansible_dict_to_boto3_filter_list(filters)

    marker = ''
    results = list()
    while True:
        try:
            response = conn.describe_db_instances(Marker=marker, **params)
            results.extend(response['DBInstances'])
            marker = response.get('Marker')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'DBInstanceNotFound':
                break
            module.fail_json_aws(e, "trying to get instance information")
        if not marker:
            break

    # Get tags for each response
    for instance in results:
        instance['tags'] = boto3_tag_list_to_ansible_dict(
            conn.list_tags_for_resource(
                ResourceName=instance['DBInstanceArn'])['TagList'])

    module.exit_json(
        changed=False, db_instances=[
            RDSDBInstance(instance).data for instance in results])


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            name=dict(aliases=['instance_name']),
            filters=dict(type='list', default=[])
        ),
        supports_check_mode=True,
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(
            msg="Region not specified. Unable to determine region from configuration.")

    # connect to the rds endpoint
    try:
        conn = boto3_conn(module, 'client', 'rds', region, **aws_connect_params)
    except Exception as e:
        module.fail_json_aws(e, msg="trying to connect to AWS")

    instance_facts(module, conn)


if __name__ == '__main__':
    main()
