#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: redshift_iam_roles
short_description: This module adds/removes IAM roles to/from Redshift clusters.
version_added: 2.6
author: Aaron Smith (@slapula)
description:
    - "This module adds or removes a list of IAM roles to a give Redshift Cluster"
options:
    cluster:
        description:
            - "This is the cluster you'd like to modify."
        required: true
    state:
        description:
            - "Desired state of the list of IAM roles on the given Redshift cluster."
        required: false
        choices: ['present', 'absent']
    roles:
        description:
            - "This is a list of IAM roles (Full ARN) to add/remove to or from the Redshift cluster."
        required: false
    purge_roles:
        description:
            - "Purges all roles from a given Redshift cluster."
        required: false
        type: bool
        default: 'no'
extends_documentation_fragment:
    - ec2
    - aws
'''

EXAMPLES = '''
- name: add IAM roles to a redshift cluster
  redshift_iam_roles:
    cluster: "staging"
    state: present
    roles:
        - "arn:aws:iam::123456789012:role/superuser"
        - "arn:aws:iam::123456789012:role/new_hotness"

- name: remove specific roles from a redshift cluster
  redshift_iam_roles:
    cluster: "staging"
    state: absent
    roles:
        - "arn:aws:iam::123456789012:role/remove_this"

- name: remove all IAM roles from a redshift cluster
  redshift_iam_roles:
    cluster: "staging"
    purge_roles: True
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, ec2_argument_spec, get_aws_connection_info, camel_dict_to_snake_dict, HAS_BOTO3
import traceback

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            cluster=dict(type='str', required=True),
            state=dict(type='str', required=False, choices=['present', 'absent']),
            roles=dict(type='list', required=False),
            purge_roles=dict(type='bool', required=False, default=False)
        )
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    target_cluster = module.params.get('cluster')
    desired_state = module.params.get('state')
    target_roles = module.params.get('roles')

    result = {
        'changed': False
    }

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    conn = boto3_conn(module, conn_type='client', resource='redshift', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    cluster_roles = conn.describe_clusters(ClusterIdentifier=target_cluster)['Clusters'][0]['IamRoles']
    current_roles = [x['IamRoleArn'] for x in cluster_roles]

    if purge_roles == True:
        if desired_state or target_roles:
            module.fail_json_aws(msg="Unable to modify IAM role(s)")
        if not current_roles:
            module.exit_json(**result)
        try:
            response = conn.modify_cluster_iam_roles(
                ClusterIdentifier=target_cluster,
                RemoveIamRoles=current_roles
            )
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(msg="Unable to modify IAM role(s): {0}".format(e))

    if desired_state == 'present':
        if not target_roles:
            module.exit_json(**result)
        try:
            response = conn.modify_cluster_iam_roles(
                ClusterIdentifier=target_cluster,
                AddIamRoles=target_roles
            )
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(msg="Unable to modify IAM role(s): {0}".format(e))

    if desired_state == 'absent':
        if not target_roles:
            module.exit_json(**result)
        try:
            response = conn.modify_cluster_iam_roles(
                ClusterIdentifier=target_cluster,
                RemoveIamRoles=target_roles
            )
            result['changed'] = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(msg="Unable to modify IAM role(s): {0}".format(e))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
