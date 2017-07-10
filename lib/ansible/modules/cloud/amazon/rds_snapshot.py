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
    required: false
  wait:
    description:
      - Whether or not to wait for snapshot creation or deletion
    required: false
    default: "no"
    choices: [ "yes", "no" ]
  wait_timeout:
    description:
      - how long before wait gives up, in seconds
    default: 300
  tags:
    description:
      - tags dict to apply to a snapshot.
    required: false
    default: null
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

import botocore
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn
from ansible.module_utils.aws.rds import RDSSnapshot, get_db_snapshot

# FIXME: the command stuff needs a 'state' like alias to make things consistent -- MPD


def await_resource(conn, resource, status, module):
    wait_timeout = module.params.get('wait_timeout') + time.time()
    while wait_timeout > time.time() and resource.status != status:
        time.sleep(5)
        if wait_timeout <= time.time():
            module.fail_json(msg="Timeout waiting for RDS resource %s" % resource.name)
        # Temporary until all the rds2 commands have their responses parsed
        if resource.name is None:
            module.fail_json(
                msg="There was a problem waiting for RDS snapshot %s" %
                resource.snapshot)
        resource = get_db_snapshot(conn, resource.name)
    return resource


def delete_snapshot(module, conn):
    snapshot = module.params.get('snapshot')

    result = get_db_snapshot(conn, snapshot)
    if not result:
        module.exit_json(changed=False)
    if result.status == 'deleting':
        module.exit_json(changed=False)
    try:
        result = conn.delete_db_snapshot(DBSnapshotIdentifier=snapshot)
    except Exception as e:
        module.fail_json(msg="Failed to delete snapshot: %s" % e.message)

    # If we're not waiting for a delete to complete then we're all done
    # so just return
    if not module.params.get('wait'):
        module.exit_json(changed=True)
    try:
        await_resource(conn, result, 'deleted', module)
        module.exit_json(changed=True)
    except Exception as e:
        if e.response['Error']['Code'] == 'DBSnapshotNotFound':
            module.exit_json(changed=True)
        else:
            module.fail_json(msg=e.message)


def create_snapshot(module, conn):
    instance_name = module.params.get('instance_name')
    if not instance_name:
        module.fail_json(msg='instance_name is required for rds_snapshot when state=present')
    snapshot_name = module.params.get('snapshot')
    changed = False
    snapshot = get_db_snapshot(conn, snapshot_name)
    if not snapshot:
        try:
            resource = conn.create_db_snapshot(DBSnapshotIdentifier=snapshot_name,
                                               DBInstanceIdentifier=instance_name)
            snapshot = RDSSnapshot(resource['DBSnapshot'])
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=e.message)

    if module.params.get('wait'):
        snapshot = await_resource(conn, snapshot, 'available', module)
    else:
        snapshot = get_db_snapshot(conn, snapshot_name)

    module.exit_json(changed=changed, snapshot=snapshot.data)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(choices=['present', 'absent'], default='present'),
            snapshot=dict(required=True),
            instance_name=dict(),
            wait=dict(type='bool', default=False),
            wait_timeout=dict(type='int', default=300),
            tags=dict(type='dict', required=False),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg="Region not specified. Unable to determine region from EC2_REGION.")

    # connect to the rds endpoint
    conn = boto3_conn(module, 'client', 'rds', region, **aws_connect_params)

    if module.params['state'] == 'absent':
        delete_snapshot(module, conn)
    else:
        create_snapshot(module, conn)


main()
