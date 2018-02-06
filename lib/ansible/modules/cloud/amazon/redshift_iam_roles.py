#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
module: redshift_iam_roles
short_description: This module adds/removes IAM roles to/from Redshift clusters.
version_added: 2.4
description:
    - "This module adds or removes a list of IAM roles to a give Redshift Cluster"
options:
    cluster:
        description:
            - "This is the cluster you'd like to modify"
        required: true
    state:
        description:
            - "Desired state of the list of IAM roles on the give Redshift cluster"
        required: true
    roles:
        description:
            - "This is a list of IAM roles (Full ARN) to add to a given Redshift cluster.  Roles attached to the cluster that are not on the list will be removed."
        required: true
'''

EXAMPLES = '''
- name: add IAM roles to a redshift cluster
  redshift_iam_roles:
    cluster: "staging"
    state: present
    roles:
        - "arn:aws:iam::123456789012:role/superuser"
        - "arn:aws:iam::123456789012:role/new_hotness"

- name: remove all IAM roles from a redshift cluster
  redshift_iam_roles:
    cluster: "staging"
    state: absent
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, camel_dict_to_snake_dict, HAS_BOTO3
import boto3
import traceback

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # will be detected by imported HAS_BOTO3

def main():
    client = boto3.client('redshift')

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            cluster=dict(type='str', required=True, aliases=['cluster_name']),
            state=dict(type='str', required=True, choices=['present', 'absent'], default='present'),
            roles=dict(type='list', required=True, default=[])
        )
    )

    module = AnsibleModule(
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

    cluster_roles = client.describe_clusters(ClusterIdentifier=target_cluster)['Clusters'][0]['IamRoles']
    current_roles = [x['IamRoleArn'] for x in cluster_roles]

    if desired_state == 'present':
        roles_to_add = list(set(target_roles) - set(current_roles))
        roles_to_remove = list(set(current_roles) - set(target_roles))
        if not definitive_roles:
            module.exit_json(**result)
        try:
            response = client.modify_cluster_iam_roles(
                ClusterIdentifier=target_cluster,
                AddIamRoles=roles_to_add,
                RemoveIamRoles=roles_to_remove
            )
            result['changed'] = True
        except:
            module.fail_json(msg="Unable to modify IAM role(s): {0}".format(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if desired_state == 'absent':
        if not matching_roles:
            module.exit_json(**result)
        try:
            response = client.modify_cluster_iam_roles(
                ClusterIdentifier=target_cluster,
                RemoveIamRoles=current_roles
            )
            result['changed'] = True
        except:
            module.fail_json(msg="Unable to modify IAM role(s): {0}".format(e),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    module.exit_json(**result)

if __name__ == '__main__':
    main()
