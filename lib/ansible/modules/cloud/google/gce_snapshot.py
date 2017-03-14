#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gce_snapshot
version_added: "2.3"
short_description: Create or destroy snapshots for GCE storage volumes
description:
  - Manages snapshots for GCE instances. This module manages snapshots for
    the storage volumes of a GCE compute instance. If there are multiple
    volumes, each snapshot will be prepended with the disk name
options:
  instance_name:
    description:
      - The GCE instance to snapshot
    required: True
  snapshot_name:
    description:
      - The name of the snapshot to manage
  disks:
    description:
      - A list of disks to create snapshots for. If none is provided,
        all of the volumes will be snapshotted
    default: all
    required: False
  state:
    description:
      - Whether a snapshot should be C(present) or C(absent)
    required: false
    default: present
    choices: [present, absent]
  service_account_email:
    description:
      - GCP service account email for the project where the instance resides
    required: true
  credentials_file:
    description:
      - The path to the credentials file associated with the service account
    required: true
  project_id:
    description:
      - The GCP project ID to use
    required: true
requirements:
    - "python >= 2.6"
    - "apache-libcloud >= 0.19.0"
author: Rob Wagner (@robwagner33)
'''

EXAMPLES = '''
- name: Create gce snapshot
  gce_snapshot:
    instance_name: example-instance
    snapshot_name: example-snapshot
    state: present
    service_account_email: project_name@appspot.gserviceaccount.com
    credentials_file: /path/to/credentials
    project_id: project_name
  delegate_to: localhost

- name: Delete gce snapshot
  gce_snapshot:
    instance_name: example-instance
    snapshot_name: example-snapshot
    state: absent
    service_account_email: project_name@appspot.gserviceaccount.com
    credentials_file: /path/to/credentials
    project_id: project_name
  delegate_to: localhost

# This example creates snapshots for only two of the available disks as
# disk0-example-snapshot and disk1-example-snapshot
- name: Create snapshots of specific disks
  gce_snapshot:
    instance_name: example-instance
    snapshot_name: example-snapshot
    state: present
    disks:
      - disk0
      - disk1
    service_account_email: project_name@appspot.gserviceaccount.com
    credentials_file: /path/to/credentials
    project_id: project_name
  delegate_to: localhost
'''

RETURN = '''
snapshots_created:
    description: List of newly created snapshots
    returned: When snapshots are created
    type: list
    sample: "[disk0-example-snapshot, disk1-example-snapshot]"

snapshots_deleted:
    description: List of destroyed snapshots
    returned: When snapshots are deleted
    type: list
    sample: "[disk0-example-snapshot, disk1-example-snapshot]"

snapshots_existing:
    description: List of snapshots that already existed (no-op)
    returned: When snapshots were already present
    type: list
    sample: "[disk0-example-snapshot, disk1-example-snapshot]"

snapshots_absent:
    description: List of snapshots that were already absent (no-op)
    returned: When snapshots were already absent
    type: list
    sample: "[disk0-example-snapshot, disk1-example-snapshot]"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gce import gce_connect

try:
    from libcloud.compute.types import Provider
    _ = Provider.GCE
    HAS_LIBCLOUD = True
except ImportError:
    HAS_LIBCLOUD = False


def find_snapshot(volume, name):
    '''
    Check if there is a snapshot already created with the given name for
    the passed in volume.

    Args:
        volume: A gce StorageVolume object to manage
        name: The name of the snapshot to look for

    Returns:
        The VolumeSnapshot object if one is found
    '''
    found_snapshot = None
    snapshots = volume.list_snapshots()
    for snapshot in snapshots:
        if name == snapshot.name:
            found_snapshot = snapshot
    return found_snapshot


def main():
    module = AnsibleModule(
        argument_spec=dict(
            instance_name=dict(required=True),
            snapshot_name=dict(required=True),
            state=dict(choices=['present', 'absent'], default='present'),
            disks=dict(default=None, type='list'),
            service_account_email=dict(type='str'),
            credentials_file=dict(type='path'),
            project_id=dict(type='str')
        )
    )

    if not HAS_LIBCLOUD:
        module.fail_json(msg='libcloud with GCE support (0.19.0+) is required for this module')

    gce = gce_connect(module)

    instance_name = module.params.get('instance_name')
    snapshot_name = module.params.get('snapshot_name')
    disks = module.params.get('disks')
    state = module.params.get('state')

    json_output = dict(
        changed=False,
        snapshots_created=[],
        snapshots_deleted=[],
        snapshots_existing=[],
        snapshots_absent=[]
    )

    snapshot = None

    instance = gce.ex_get_node(instance_name, 'all')
    instance_disks = instance.extra['disks']

    for instance_disk in instance_disks:
        device_name = instance_disk['deviceName']
        if disks is None or device_name in disks:
            volume_obj = gce.ex_get_volume(device_name)

            # If we have more than one disk to snapshot, prepend the disk name
            if len(instance_disks) > 1:
                snapshot_name = device_name + "-" + snapshot_name

            snapshot = find_snapshot(volume_obj, snapshot_name)

            if snapshot and state == 'present':
                json_output['snapshots_existing'].append(snapshot_name)

            elif snapshot and state == 'absent':
                snapshot.destroy()
                json_output['changed'] = True
                json_output['snapshots_deleted'].append(snapshot_name)

            elif not snapshot and state == 'present':
                volume_obj.snapshot(snapshot_name)
                json_output['changed'] = True
                json_output['snapshots_created'].append(snapshot_name)

            elif not snapshot and state == 'absent':
                json_output['snapshots_absent'].append(snapshot_name)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
