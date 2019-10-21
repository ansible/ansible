#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: dms_replication_subnet_group
short_description: creates or destroys a data migration services subnet group
description:
    - Creates or destroys a data migration services subnet group
version_added: "2.9"
options:
    state:
        description:
            - State of the subnet group
        default: present
        choices: ['present', 'absent']
        type: str
    identifier:
        description:
            - The name for the replication subnet group.
              This value is stored as a lowercase string.
              Must contain no more than 255 alphanumeric characters,
              periods, spaces, underscores, or hyphens. Must not be "default".
        type: str
    description:
        description:
            - The description for the subnet group.
        type: str
    subnet_ids:
        description:
            - A list containing the subnet ids for the replication subnet group,
              needs to be at least 2 items in the list
        type: list
author:
    - "Rui Moreira (@ruimoreira)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- dms_replication_subnet_group:
    state: present
    identifier: "dev-sngroup"
    description: "Development Subnet Group asdasdas"
    subnet_ids: ['subnet-id1','subnet-id2']
'''

RETURN = ''' # '''
__metaclass__ = type
import traceback
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, HAS_BOTO3, \
    camel_dict_to_snake_dict, get_aws_connection_info, AWSRetry
try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

backoff_params = dict(tries=5, delay=1, backoff=1.5)


@AWSRetry.backoff(**backoff_params)
def describe_subnet_group(connection, subnet_group):
    """checks if instance exists"""
    try:
        subnet_group_filter = dict(Name='replication-subnet-group-id',
                                   Values=[subnet_group])
        return connection.describe_replication_subnet_groups(Filters=[subnet_group_filter])
    except botocore.exceptions.ClientError:
        return {'ReplicationSubnetGroups': []}


@AWSRetry.backoff(**backoff_params)
def replication_subnet_group_create(connection, **params):
    """ creates the replication subnet group """
    return connection.create_replication_subnet_group(**params)


@AWSRetry.backoff(**backoff_params)
def replication_subnet_group_modify(connection, **modify_params):
    return connection.modify_replication_subnet_group(**modify_params)


@AWSRetry.backoff(**backoff_params)
def replication_subnet_group_delete(module, connection):
    subnetid = module.params.get('identifier')
    delete_parameters = dict(ReplicationSubnetGroupIdentifier=subnetid)
    return connection.delete_replication_subnet_group(**delete_parameters)


def get_dms_client(module, aws_connect_params, client_region, ec2_url):
    client_params = dict(
        module=module,
        conn_type='client',
        resource='dms',
        region=client_region,
        endpoint=ec2_url,
        **aws_connect_params
    )
    return boto3_conn(**client_params)


def replication_subnet_exists(subnet):
    """ Returns boolean based on the existence of the endpoint
    :param endpoint: dict containing the described endpoint
    :return: bool
    """
    return bool(len(subnet['ReplicationSubnetGroups']))


def create_module_params(module):
    """
    Reads the module parameters and returns a dict
    :return: dict
    """
    instance_parameters = dict(
        # ReplicationSubnetGroupIdentifier gets translated to lower case anyway by the API
        ReplicationSubnetGroupIdentifier=module.params.get('identifier').lower(),
        ReplicationSubnetGroupDescription=module.params.get('description'),
        SubnetIds=module.params.get('subnet_ids'),
    )

    return instance_parameters


def compare_params(module, param_described):
    """
    Compares the dict obtained from the describe function and
    what we are reading from the values in the template We can
    never compare passwords as boto3's method for describing
    a DMS endpoint does not return the value for
    the password for security reasons ( I assume )
    """
    modparams = create_module_params(module)
    changed = False
    # need to sanitize values that get returned from the API
    if 'VpcId' in param_described.keys():
        param_described.pop('VpcId')
    if 'SubnetGroupStatus' in param_described.keys():
        param_described.pop('SubnetGroupStatus')
    for paramname in modparams.keys():
        if paramname in param_described.keys() and \
                param_described.get(paramname) == modparams[paramname]:
            pass
        elif paramname == 'SubnetIds':
            subnets = []
            for subnet in param_described.get('Subnets'):
                subnets.append(subnet.get('SubnetIdentifier'))
            for modulesubnet in modparams['SubnetIds']:
                if modulesubnet in subnets:
                    pass
        else:
            changed = True
    return changed


def create_replication_subnet_group(module, connection):
    try:
        params = create_module_params(module)
        return replication_subnet_group_create(connection, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to create DMS replication subnet group.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to create DMS replication subnet group.",
                         exception=traceback.format_exc())


def modify_replication_subnet_group(module, connection):
    try:
        modify_params = create_module_params(module)
        return replication_subnet_group_modify(connection, **modify_params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to Modify the DMS replication subnet group.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to Modify the DMS replication subnet group.",
                         exception=traceback.format_exc())


def main():
    argument_spec = dict(
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        identifier=dict(type='str', required=True),
        description=dict(type='str', required=True),
        subnet_ids=dict(type='list', elements='str', required=True),
    )
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    exit_message = None
    changed = False
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    aws_config_region, ec2_url, aws_connect_params = \
        get_aws_connection_info(module, boto3=True)
    dmsclient = get_dms_client(module, aws_connect_params, aws_config_region, ec2_url)
    subnet_group = describe_subnet_group(dmsclient,
                                         module.params.get('identifier'))
    if state == 'present':
        if replication_subnet_exists(subnet_group):
            if compare_params(module, subnet_group["ReplicationSubnetGroups"][0]):
                if not module.check_mode:
                    exit_message = modify_replication_subnet_group(module, dmsclient)
                else:
                    exit_message = dmsclient
                changed = True
            else:
                exit_message = "No changes to Subnet group"
        else:
            if not module.check_mode:
                exit_message = create_replication_subnet_group(module, dmsclient)
                changed = True
            else:
                exit_message = "Check mode enabled"

    elif state == 'absent':
        if replication_subnet_exists(subnet_group):
            if not module.check_mode:
                replication_subnet_group_delete(module, dmsclient)
                changed = True
                exit_message = "Replication subnet group Deleted"
            else:
                exit_message = dmsclient
                changed = True

        else:
            changed = False
            exit_message = "Replication subnet group does not exist"

    module.exit_json(changed=changed, msg=exit_message)


if __name__ == '__main__':
    main()
