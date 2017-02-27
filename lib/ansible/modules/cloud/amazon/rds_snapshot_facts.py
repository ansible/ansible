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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: rds_snapshot_facts
version_added: "2.3"
short_description: obtain facts about one or more RDS snapshots
description:
  - obtain facts about one or more RDS snapshots
options:
  name:
    description:
      - Name of an RDS snapshot. Mutually exclusive with I(instance_name)
    required: false
    aliases:
      - snapshot_name
  instance_name:
    description:
      - RDS instance name for which to find snapshots. Mutually exclusive with I(name)
    required: false
  snapshot_type:
    description:
      - Type of snapshot to find. By default both automated and manual
        snapshots will be returned.
    required: false
    choices: ['automated', 'manual', 'shared', 'public']

requirements:
    - "python >= 2.6"
    - "boto3"
author:
    - "Will Thames (@willthames)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Get facts about an snapshot
- rds_snapshot_facts:
    name: snapshot_name
  register: new_database_facts

# Get all RDS snapshots for an RDS instance
- rds_snapshot_facts:
    instance_name: helloworld-rds-master
'''

RETURN = '''
snapshots:
    description: zero or more snapshots that match the (optional) parameters
    type: list
    returned: always
    sample:
       "snapshots": [
           {
               "availability_zone": "ap-southeast-2b",
               "create_time": "2017-02-23T19:36:26.303000+00:00",
               "id": "rds:helloworld-rds-master-2017-02-23-19-36",
               "instance_created": "2017-02-16T23:04:16.619000+00:00",
               "instance_id": "helloworld-rds-master",
               "snapshot_type": "automated",
               "status": "available"
           }
       ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn, HAS_BOTO3
from ansible.module_utils.ec2 import ansible_dict_to_boto3_filter_list, camel_dict_to_snake_dict
from ansible.module_utils.rds import RDSSnapshot

import traceback

try:
    import botocore
except:
    pass  # caught by imported HAS_BOTO3


def snapshot_facts(module, conn):
    snapshot_name = module.params.get('name')
    snapshot_type = module.params.get('snapshot_type')
    instance_name = module.params.get('instance_name')

    params = dict()
    if snapshot_name:
        params['DBSnapshotIdentifier'] = snapshot_name
    if instance_name:
        params['DBInstanceIdentifier'] = instance_name
    if snapshot_type:
        params['SnapshotType'] = snapshot_type
        if snapshot_type == 'public':
            params['IsPublic'] = True
        elif snapshot_type == 'shared':
            params['IsShared'] = True

    marker = ''
    results = list()
    while True:
        try:
            response = conn.describe_db_snapshots(Marker=marker, **params)
            results.extend(response['DBSnapshots'])
            marker = response.get('Marker')
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'DBSnapshotNotFound':
                break
            module.fail_json(msg=str(e), exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        if not marker:
            break

    module.exit_json(changed=False, snapshots=[RDSSnapshot(snapshot).data for snapshot in results])


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name = dict(aliases=['snapshot_name']),
            instance_name = dict(),
            snapshot_type = dict(choices=['automated', 'manual', 'shared', 'public'])
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[['name', 'instance_name']],
    )

    if not HAS_BOTO3:
        module.fail_json(msg="botocore and boto3 are required for rds_facts module")

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="Region not specified. Unable to determine region from configuration.")

    # connect to the rds endpoint
    conn = boto3_conn(module, 'client', 'rds', region, **aws_connect_params)

    snapshot_facts(module, conn)


main()
