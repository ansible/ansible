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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: dms_replication_subnet_group
short_description: creates or destroys a data migration services subnet group
description:
    - creates or destroys a data migration services subnet group
version_added: "2.9"
options:
    state:
        description:
            - State of the subnet group
        default: present
        choices: ['present', 'absent']
    subnetgroupidentifier:
        description:
            - The name for the replication subnet group.
              This value is stored as a lowercase string.
              Must contain no more than 255 alphanumeric characters,
              periods, spaces, underscores, or hyphens. Must not be "default".
    subnetgroupdescription:
        description:
            - The description for the subnet group.
    subnetids:
        description:
            - A list containing the subnet ids for the replication subnet group,
              needs to be at least 2 items in the list
author:
    - "Rui Moreira (@ruimoreira)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
- dms_replication_subnet_group:
    state: present
    subnetgroupidentifier: "dev-sngroup"
    subnetgroupdescription: "Development Subnet Group asdasdas"
    subnetids: ['subnet-id1','subnet-id2']
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
def replication_subnet_group_delete(connection):
    subnetid = module.params.get('subnetgroupidentifier')
    delete_parameters = dict(ReplicationSubnetGroupIdentifier=subnetid)
    return connection.delete_replication_subnet_group(**delete_parameters)


def get_dms_client(aws_connect_params, client_region, ec2_url):
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
    """ Returns boolean based on the existance of the endpoint
    :param endpoint: dict containing the described endpoint
    :return: bool
    """
    return bool(len(subnet['ReplicationSubnetGroups']))


def create_module_params():
    """
    Reads the module parameters and returns a dict
    :return: dict
    """
    instance_parameters = dict(
        # ReplicationSubnetGroupIdentifier gets translated to lower case anyway by the API
        ReplicationSubnetGroupIdentifier=module.params.get('subnetgroupidentifier').lower(),
        ReplicationSubnetGroupDescription=module.params.get('subnetgroupdescription'),
        SubnetIds=module.params.get('subnetids'),
    )

    return instance_parameters


def compare_params(param_described):
    """
    Compares the dict obtained from the describe function and
    what we are reading from the values in the template We can
    never compare passwords as boto3's method for describing
    a DMS endpoint does not return the value for
    the password for security reasons ( I assume )
    """
    modparams = create_module_params()
    changed = False
    # need to sanitize values that get retured from the API
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


def create_replication_subnet_group(connection):
    try:
        params = create_module_params()
        return replication_subnet_group_create(connection, **params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to create DMS replication subnet group.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to create DMS replication subnet group.",
                         exception=traceback.format_exc())


def modify_replication_subnet_group(connection):
    try:
        modify_params = create_module_params()
        return replication_subnet_group_modify(connection, **modify_params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Failed to Modify the DMS replication subnet group.",
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Failed to Modify the DMS replication subnet group.",
                         exception=traceback.format_exc())


def delete_replication_subnet_group(connection):
    return True


def main():
    argument_spec = dict(
        state=dict(choices=['present', 'absent'], default='present'),
        subnetgroupidentifier=dict(required=True),
        subnetgroupdescription=dict(required=True),
        subnetids=dict(type='list', required=True),
    )
    global module
    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=[],
        supports_check_mode=False
    )
    exit_message = None
    changed = False
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    state = module.params.get('state')
    aws_config_region, ec2_url, aws_connect_params = \
        get_aws_connection_info(module, boto3=True)
    dmsclient = get_dms_client(aws_connect_params, aws_config_region, ec2_url)
    subnet_group = describe_subnet_group(dmsclient,
                                         module.params.get('subnetgroupidentifier'))
    if state == 'present':
        if replication_subnet_exists(subnet_group):
            if compare_params(subnet_group["ReplicationSubnetGroups"][0]):
                changed = True
                exit_message = modify_replication_subnet_group(dmsclient)
            else:
                exit_message = "No changes to Subnet group"
        else:
            exit_message = create_replication_subnet_group(dmsclient)
            changed = True
    elif state == 'absent':
        if replication_subnet_exists(subnet_group):
            changed = True
            replication_subnet_group_delete(dmsclient)
            exit_message = "Replication subnet group Deleted"

        else:
            changed = False
            exit_message = "Replication subnet group does not exist"

    module.exit_json(changed=changed, msg=exit_message)


if __name__ == '__main__':
    main()
