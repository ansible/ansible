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
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: rds_snapshot
version_added: "2.4"
short_description: manage Amazon RDS snapshots
description:
     - Creates or deletes RDS snapshots.
options:
  state:
    description:
      - Specify the desired state of the snapshot
    default: present
    choices: [ 'present', 'absent']
  snapshot:
    description:
      - Name of snapshot to manage
    required: true
  instance_name:
    description:
      - Database instance identifier. Required when state is present
  wait:
    description:
      - Whether or not to wait for snapshot creation or deletion
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
  tags:
    description:
      - tags dict to apply to a snapshot.
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
# Create snapshot
- rds_snapshot:
    instance_name: new-database
    snapshot: new-database-snapshot

# Delete snapshot
- rds_snapshot:
    snapshot: new-database-snapshot
    state: absent

- debug:
    msg: "The new db endpoint is {{ rds.instance.endpoint }}"
'''

RETURN = '''
snapshot:
  description: the information returned in data from boto3 get_db_snapshot
  returned: success
  type: dict
'''

try:
    import botocore
except ImportError:
    pass  # protected by AnsibleAWSModule

import time

# import module snippets
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import get_aws_connection_info, boto3_conn, camel_dict_to_snake_dict
from ansible.module_utils.aws.rds import get_db_snapshot


def await_snapshot(conn, snapshot, status, module):
    wait_timeout = module.params.get('wait_timeout') + time.time()
    while wait_timeout > time.time() and snapshot['status'] != status:
        time.sleep(5)
        if wait_timeout <= time.time():
            module.fail_json(msg="Timeout waiting for RDS snapshot %s" % snapshot['db_snapshot_identifier'])
        # Temporary until all the rds2 commands have their responses parsed
        if snapshot['db_snapshot_identifier'] is None:
            module.fail_json(msg="Failed waiting for RDS snapshot %s" % snapshot['db_snapshot_identifier'])
        try:
            snapshot = get_db_snapshot(conn, snapshot['db_snapshot_identifier'])
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e, msg="Couldn't retrieve snapshot")
    return snapshot


def delete_snapshot(module, conn):
    snapshot = module.params.get('snapshot')

    try:
        result = get_db_snapshot(conn, snapshot)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="Couldn't retrieve snapshot")
    if not result:
        module.exit_json(changed=False)
    if result['status'] == 'deleting':
        module.exit_json(changed=False)
    try:
        result = conn.delete_db_snapshot(DBSnapshotIdentifier=snapshot)
    except Exception as e:
        module.fail_json_aws(e, msg="trying to delete snapshot")

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not module.params.get('wait'):
        module.exit_json(changed=True)
    try:
        await_snapshot(conn, result, 'deleted', module)
        module.exit_json(changed=True)
    except Exception as e:
        if e.response['Error']['Code'] == 'DBSnapshotNotFound':
            module.exit_json(changed=True)
        else:
            module.fail_json_aws(e, "awaiting snapshot deletion")


def create_snapshot(module, conn):
    instance_name = module.params.get('instance_name')
    if not instance_name:
        module.fail_json(msg='instance_name is required for rds_snapshot when state=present')
    snapshot_name = module.params.get('snapshot')
    changed = False
    try:
        snapshot = get_db_snapshot(conn, snapshot_name)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e, msg="Couldn't retrieve snapshot")
    if not snapshot:
        try:
            resource = conn.create_db_snapshot(DBSnapshotIdentifier=snapshot_name,
                                               DBInstanceIdentifier=instance_name)
            snapshot = camel_dict_to_snake_dict(resource['DBSnapshot'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e, msg="trying to create db snapshot")

    if module.params.get('wait'):
        snapshot = await_snapshot(conn, snapshot, 'available', module)
    else:
        try:
            snapshot = get_db_snapshot(conn, snapshot_name)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e, msg="Couldn't retrieve snapshot")

    module.exit_json(changed=changed, snapshot=snapshot)


def main():
    module = AnsibleAWSModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            snapshot=dict(required=True),
            instance_name=dict(),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300),
            tags=dict(type='dict'),
        )
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="Region not specified. Unable to determine region from EC2_REGION.")

    # connect to the rds endpoint
    try:
        conn = boto3_conn(module, 'client', 'rds', region, **aws_connect_params)
    except Exception as e:
        module.fail_json_aws(e, msg="trying to create db snapshot")

    if module.params['state'] == 'absent':
        delete_snapshot(module, conn)
    else:
        create_snapshot(module, conn)


main()
