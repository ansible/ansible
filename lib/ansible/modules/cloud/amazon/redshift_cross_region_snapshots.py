#!/usr/bin/python

# Copyright: (c) 2018, JR Kerkstra <jrkerkstra@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: redshift_cross_region_snapshots
short_description: Manage Redshift Cross Region Snapshots
description:
  - Manage Redshift Cross Region Snapshots. Supports KMS-Encrypted Snapshots.
  - For more information, see https://docs.aws.amazon.com/redshift/latest/mgmt/working-with-snapshots.html#cross-region-snapshot-copy
version_added: "2.8"
author: JR Kerkstra (@captainkerk)
options:
  cluster_name:
    description:
      - The name of the cluster to configure cross-region snapshots for.
    required: true
    aliases: [ "cluster" ]
  state:
    description:
      - Create or remove the cross-region snapshot configuration.
    required: true
    choices: [ "present", "absent" ]
    default: present
  region:
    description:
      - The clusters region
    required: true
    aliases: [ "source" ]
  destination_region:
    description:
      - The region to copy snapshots to
    required: true
    aliases: [ "destination" ]
  snapshot_copy_grant:
    description:
      - A grant for Amazon Redshift to use a master key in the destination region.
      - See http://boto3.readthedocs.io/en/latest/reference/services/redshift.html#Redshift.Client.create_snapshot_copy_grant
    required: false
    aliases: [ "copy_grant" ]
  snapshot_retention_period:
    description:
      - Keep cross-region snapshots for N number of days
    required: true
    aliases: [ "retention_period" ]
requirements: [ "botocore", "boto3" ]
extends_documentation_fragment:
  - ec2
  - aws
'''

EXAMPLES = '''
- name: configure cross-region snapshot on cluster `johniscool`
  redshift_cross_region_snapshots:
    cluster_name: johniscool
    state: present
    region: us-east-1
    destination_region: us-west-2
    retention_period: 1

- name: configure cross-region snapshot on kms-encrypted cluster
  redshift_cross_region_snapshots:
    cluster_name: whatever
    state: present
    source: us-east-1
    destination: us-west-2
    copy_grant: 'my-grant-in-destination'
    retention_period: 10

- name: disable cross-region snapshots, necessary before most cluster modifications (rename, resize)
  redshift_cross_region_snapshots:
    cluster_name: whatever
    state: absent
    region: us-east-1
    destination_region: us-west-2
'''

RETURN = ''' # '''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import ec2_argument_spec


class SnapshotController(object):

    def __init__(self, client, cluster_name):
        self.client = client
        self.cluster_name = cluster_name

    def get_cluster_snapshot_copy_status(self):
        response = self.client.describe_clusters(
            ClusterIdentifier=self.cluster_name
        )
        return response['Clusters'][0].get('ClusterSnapshotCopyStatus')

    def enable_snapshot_copy(self, destination_region, grant_name, retention_period):
        if grant_name:
            self.client.enable_snapshot_copy(
                ClusterIdentifier=self.cluster_name,
                DestinationRegion=destination_region,
                RetentionPeriod=retention_period,
                SnapshotCopyGrantName=grant_name,
            )
        else:
            self.client.enable_snapshot_copy(
                ClusterIdentifier=self.cluster_name,
                DestinationRegion=destination_region,
                RetentionPeriod=retention_period,
            )

    def disable_snapshot_copy(self):
        self.client.disable_snapshot_copy(
            ClusterIdentifier=self.cluster_name
        )

    def modify_snapshot_copy_retention_period(self, retention_period):
        self.client.modify_snapshot_copy_retention_period(
            ClusterIdentifier=self.cluster_name,
            RetentionPeriod=retention_period
        )


def requesting_unsupported_modifications(actual, requested):
    if (actual['SnapshotCopyGrantName'] != requested['snapshot_copy_grant'] or
            actual['DestinationRegion'] != requested['destination_region']):
        return True
    return False


def needs_update(actual, requested):
    if actual['RetentionPeriod'] != requested['snapshot_retention_period']:
        return True
    return False


def run_module():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            cluster_name=dict(type='str', required=True, aliases=['cluster']),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            region=dict(type='str', required=True, aliases=['source']),
            destination_region=dict(type='str', required=True, aliases=['destination']),
            snapshot_copy_grant=dict(type='str', aliases=['copy_grant']),
            snapshot_retention_period=dict(type='int', required=True, aliases=['retention_period']),
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        message=''
    )
    connection = module.client('redshift')

    snapshot_controller = SnapshotController(client=connection,
                                             cluster_name=module.params.get('cluster_name'))

    current_config = snapshot_controller.get_cluster_snapshot_copy_status()
    if current_config is not None:
        if module.params.get('state') == 'present':
            if requesting_unsupported_modifications(current_config, module.params):
                message = 'Cannot modify destination_region or grant_name. ' \
                          'Please disable cross-region snapshots, and re-run.'
                module.fail_json(msg=message, **result)
            if needs_update(current_config, module.params):
                result['changed'] = True
                if not module.check_mode:
                    snapshot_controller.modify_snapshot_copy_retention_period(
                        module.params.get('snapshot_retention_period')
                    )
        else:
            result['changed'] = True
            if not module.check_mode:
                snapshot_controller.disable_snapshot_copy()
    else:
        if module.params.get('state') == 'present':
            result['changed'] = True
            if not module.check_mode:
                snapshot_controller.enable_snapshot_copy(module.params.get('destination_region'),
                                                         module.params.get('snapshot_copy_grant'),
                                                         module.params.get('snapshot_retention_period'))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
