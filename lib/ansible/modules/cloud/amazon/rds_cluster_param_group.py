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

DOCUMENTATION = '''
module: rds_cluster_param_group
short_description: Manages RDS Aurora Cluster Parameter Groups
description:
  -Manages the creation, modification, deletion of RDS Aurora parameter groups.
version_added: "2.2"
author: "Nick Aslanidis (@naslanidis)"
options:
  param_group_name:
    description:
      - The name of the DB cluster parameter group.
    required: true
    default: null
  param_group_family:
    description:
      - The DB cluster parameter group family name.
    required: false
    default: null
  description:
    description:
      - The description for the DB cluster parameter group.
    required: false
    default: null
  params:
    description:
      - A list of parameters in the DB cluster parameter group
    required: false
    default: null
  apply_method:
    description:
      - Indicates when to apply parameter updates.
    required: false
    default: null
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Create RDS cluster param group with no parameters set
- name: Create RDS cluster param group with no parameters set
  rds_cluster_param_group:
    region: ap-southeast-2
    profile: auto_general_dev
    state: absent
    param_group_name: test-cluster-param-group
    param_group_family: aurora5.6
    description: test cluster param group
  register: rds_cluster_param_group

# Create RDS cluster param group with parameters
- name: Create RDS cluster param group with no parameters set
  rds_cluster_param_group:
    region: ap-southeast-2
    profile: auto_general_dev
    state: absent
    param_group_name: test-cluster-param-group
    param_group_family: aurora5.6
    description: test cluster param group
    params: 
      - ParameterName: binlog_format
        ParameterValue: 'STATEMENT'
        ApplyMethod: 'pending-reboot'

      - ParameterName: binlog_checksum
        ParameterValue: 'CRC32'
        ApplyMethod: 'pending-reboot'
  register: rds_cluster_param_group

# Delete RDS cluster param group
- name: Delete RDS cluster param group
  rds_cluster_param_group:
    region: ap-southeast-2
    profile: auto_general_dev
    state: absent
    param_group_name: test-cluster-param-group
  register: deleted_rds_cluster_param_group
'''

RETURN = '''
DBClusterParameterGroups:
  DBClusterParameterGroupName:
    description: Provides the name of the DB cluster parameter group.
    returned: when state=present
    type: string
    sample: "test-cluster-param-group"
  DBParameterGroupFamily:
    description: Provides the name of the DB parameter group family that this DB cluster parameter group is compatible with.
    returned: when state=present
    type: string
    sample: "aurora5.6"
  Description:
    description: Provides the customer-specified description for this DB cluster parameter group.
    returned: when state=present
    type: string
    sample: "test cluster param group"
'''

try:
    import json
    import botocore
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_cluster_param_group(client, module, param_group_name=None):
    params = dict()

    if param_group_name:
        params['DBClusterParameterGroupName'] = param_group_name
    else:
        params['DBClusterParameterGroupName'] = module.params.get('param_group_name')

    try:
        response = client.describe_db_cluster_parameter_groups(**params)

    except botocore.exceptions.ClientError as e:
        if 'DBParameterGroupNotFound' not in e.message:
            module.fail_json(msg=str(e))
        else:
            response = None

    results = response
    return results


def create_cluster_param_group(client, module):
    changed = True
    params = dict()
    params['DBClusterParameterGroupName'] = module.params.get('param_group_name')
    params['DBParameterGroupFamily'] = module.params.get('param_group_family')
    params['Description'] = str(module.params.get('description'))

    tag_array = []
    if module.params.get('tags'):
        for tag, value in module.params.get('tags').iteritems():
            tag_array.append({'Key': tag, 'Value': value})
        params['Tags'] = tag_array

    try:
        response = client.create_db_cluster_parameter_group(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))
    
    results = response
    return changed, results


def get_param_group_params(client, module):
    params = dict()
    params['DBClusterParameterGroupName'] = module.params.get('param_group_name')

    try:
        response = client.describe_db_cluster_parameters(**params)
    except botocore.exceptions.ClientError as e:
        if 'OptionGroupNotFound' not in e.message:
            module.fail_json(msg=str(e))
        else:
            response = None

    results = response
    return results


def match_param_options(client, module):
    requires_update = False
    new_params = module.params.get('params')

    current_params = get_param_group_params(client, module)
    for current_param in current_params['Parameters']:
        for new_param in new_params:
            if current_param['ParameterName'] == new_param['ParameterName']:
                if 'ParameterValue' in  current_param:
                    if current_param['ParameterValue'] != new_param['ParameterValue']:
                        requires_update = True
                else:
                    requires_update = True
   
    return requires_update


def modify_param_group_params(client, module):
    changed = True
    params = dict()
    params['DBClusterParameterGroupName'] = module.params.get('param_group_name')
    params['Parameters'] = module.params.get('params')

    try:
        response = client.modify_db_cluster_parameter_group(**params)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg=str(e))

    results = response
    return changed, results


def setup_cluster_param_group(client, module):
    results = []
    changed = False
    params = dict()

    existing_cluster_group = get_cluster_param_group(client, module)
    group_params = module.params.get('params')
    param_group_name = module.params.get('param_group_name')

    if existing_cluster_group:
        results = get_cluster_param_group(client, module)
        if group_params: 
            update_required = match_param_options(client, module)
            if update_required:
                changed, modified_group = modify_param_group_params(client, module)
                results = get_cluster_param_group(client, module)
    else:
        changed, new_param_group = create_cluster_param_group(client, module)
        results = get_cluster_param_group(client, module)

    return changed, results


def remove_cluster_param_group(client, module):
    changed = False
    params = dict()
    params['DBClusterParameterGroupName'] = module.params.get('param_group_name')

    # Check if there is an existing cluster parameter group
    existing_cluster_group = get_cluster_param_group(client, module)

    if existing_cluster_group:
        changed = True
        try:
            response = client.delete_db_cluster_parameter_group(**params)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg=str(e))
    else:
        response = None

    results = response
    return changed, results


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', required=True),
        param_group_name=dict(type='str', required=True),
        param_group_family=dict(type='str', required=False),
        description=dict(type='str', required=False),
        params=dict(type='list', required=False),
        apply_method=dict(type='str', required=False)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='json and boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        client = boto3_conn(module, conn_type='client', resource='rds', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError:
        e = get_exception()
        module.fail_json(msg="Can't authorize connection - "+str(e))

    state = module.params.get('state').lower()
    
    invocations = {
        "present": setup_cluster_param_group,
        "absent": remove_cluster_param_group
    }

    (changed, results) = invocations[state](client, module)
    module.exit_json(changed=changed, cluster_param_group=results)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
