#!/usr/bin/python
#
# This is a free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This Ansible library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: rds_facts
short_description: Gather facts about RDS instances in AWS
description:
    - Gather facts about RDS instances in AWS
version_added: "2.2"
requirements: [ boto3 ]
author: "Nick Aslanidis (@naslanidis)"
options:
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. 
      - See U(http://docs.aws.amazon.com/AmazonRDS/latest/APIReference/API_DescribeDBInstances.html) for possible filters.
      - Note: there are no currently supported filters for the DescribeDBInstances API action
    required: false
    default: null
  db_instance_identifier:
    description:
      - The user-supplied instance identifier. If this parameter is specified, information from only the specific DB instance is returned.
    required: false
    default: None
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Get facts for all RDS instances in an account
- name: Get facts for all RDS instances in an account
  rds_facts:
    region: ap-southeast-2
    profile: production
  register: all_rds_facts

# Get facts for a specific RDS instance
- name: Get specific instance facts 
  rds_facts:
    region: ap-southeast-2
    profile: production
    db_instance_identifier: test-instance
  register: rds_facts
'''

RETURN = '''

DBInstance:
  AllocatedStorage:
    description: Specifies the allocated storage size specified in gigabytes.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: integer
    sample: 10
  AutoMinorVersionUpgrade:
    description: Indicates that minor version patches are applied automatically.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: true
  AvailabilityZone:
    description: Specifies the name of the Availability Zone the DB instance is located in.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "ap-southeast-2b"
  BackupRetentionPeriod:
    description: Specifies the number of days for which automatic DB snapshots are retained.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: integer
    sample: 1
  CACertificateIdentifier:
    description: The identifier of the CA certificate for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "rds-ca-2015"
  CopyTagsToSnapshot:
    description: Specifies whether tags are copied from the DB instance to snapshots of the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  DBInstanceClass:
    description: Contains the name of the compute and memory capacity class of the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "db.t2.medium"
  DBInstanceIdentifier:
    description: Contains a user-supplied database identifier. This identifier is the unique key that identifies a DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "test-instance2"
  DBInstanceStatus:
    description: Specifies the current state of this database.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "available"
  DBName:
    description: Contains the name of the initial database of this instance that was provided at create time, if one was specified when the DB instance was created.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "null"
  DBParameterGroups:
    description: Provides the list of DB parameter groups applied to this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "test-param-group"
  DBSubnetGroup:
    description: A DB subnet group to associate with this DB instance
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "abc-sbg-prod"
  DbInstancePort:
    description: Specifies the port that the DB instance listens on. If the DB instance is part of a DB cluster, this can be a different port than the DB cluster port.
    returned: when command=create, modify, reboot, restore, replicate
    type: integer
    sample: 0
  DbiResourceId:
    description: The region-unique, immutable identifier for the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "db-C6IH24KNSUXIBDA2UNVO4BIIBY"
  Endpoint:
    description: Specifies the connection endpoint, including port, zone and hostedzoneid.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: dict
    sample: {"Address": "test-instance2.c4nb0jta2bug.ap-southeast-2.rds.amazonaws.com", "HostedZoneId": "Z32T0VXXXXXS0V", "Port": 3306"}
  Engine:
    description: Provides the name of the database engine to be used for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "mysql"
  EngineVersion:
    description: Indicates the database engine version.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "5.6.10a"
  InstanceCreateTime:
    description: Provides the date and time the DB instance was created.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: datetime
    sample: "2016-09-03T06:05:25.244000+00:00"
  LatestRestorableTime:
    description: Specifies the latest time to which a database can be restored with point-in-time restore.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: datetime
    sample: "2016-08-27T02:21:04.538000+00:00"
  LicenseModel:
    description: License model information for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "general-public-license"
  MasterUsername:
    description: Contains the master username for the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "testuser"
  MonitoringInterval:
    description: The interval, in seconds, between points when Enhanced Monitoring metrics are collected for the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: integer
    sample: 0
  MultiAZ:
    description: Specifies if the DB instance is a Multi-AZ deployment.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  OptionGroupMemberships:
    description: Provides the list of option group memberships for this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: list
    sample: [{"OptionGroupName": "test-option-group", "Status": "in-sync"}]
  PendingModifiedValues:
    description: Specifies that changes to the DB instance are pending.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: dict
    sample: {}
  PreferredBackupWindow:
    description: Specifies the daily time range during which automated backups are created if automated backups are enabled.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "18:14-18:44"
  PreferredMaintenanceWindow:
    description: Specifies the weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "tue:16:58-tue:17:28"
  PubliclyAccessible:
    description: Specifies the accessibility options for the DB instance
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  ReadReplicaDBInstanceIdentifiers:
    description: Contains one or more identifiers of the Read Replicas associated with this DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: list
    sample: []
  ReadReplicaSourceDBInstanceIdentifier:
    description: Contains the identifier of the source DB instance if this DB instance is a Read Replica.
    returned: when command=replicate
    type: string
    sample: "test-instance"
  StorageEncrypted:
    description: Specifies whether the DB instance is encrypted.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: boolean
    sample: false
  StorageType:
    description: Specifies the storage type to be associated with the DB instance.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: string
    sample: "standard"
  VpcSecurityGroups:
    description: Provides a list of VPC security groups that the DB instance belongs.
    returned: when command=create, modify, reboot, restore, replicate, promote
    type: list
    sample: [{"Status": "active", "VpcSecurityGroupId": "sg-d188c7b5"}]
'''

import json

try:
    import botocore
    import boto3   
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def list_rds_instances(client, module):
    all_rds_instances_array = []
    params = dict()

    if module.params.get('filters'):
        params['Filters'] = []
        for key, value in module.params.get('filters').iteritems():
            temp_dict = dict()
            temp_dict['Name'] = key
            if isinstance(value, basestring):
                temp_dict['Values'] = [value]
            else:
                temp_dict['Values'] = value
            params['Filters'].append(temp_dict)

    if module.params.get("db_instance_identifier"):
        params['DBInstanceIdentifier'] = module.params.get("db_instance_identifier")

    try:
        all_rds_instances = client.describe_db_instances(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    for rds_instance in all_rds_instances['DBInstances']:
        all_rds_instances_array.append(rds_instance)
     
    module.exit_json(db_instances=all_rds_instances_array)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            filters = dict(type='dict', default=None, ),
            db_instance_identifier = dict(type='str', default=None)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    # Validate Requirements
    if not HAS_BOTO3:
        module.fail_json(msg='json and botocore/boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        connection = boto3_conn(module, conn_type='client', resource='rds', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError, e:
        module.fail_json(msg="Can't authorize connection - "+str(e))

    # call your function here
    results = list_rds_instances(connection, module)
    
    module.exit_json(result=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
