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

DOCUMENTATION = """
---
module: elasticache
short_description: Manage cache security groups in Amazon Elasticache.
description:
  - Manage cache security groups in Amazon Elasticache.
  - Returns information about the specified cache cluster.
version_added: "2.3"
author: "Sloane Hertel (@s-hertel)"
options:
  group_family:
    description:
      - The name of the cache parameter group family that the cache parameter group can be used with. 
    choices: ['memcached1.4', 'redis2.6', 'redis2.8', 'redis3.2']
    required: yes
    type: string
  name:
    description:
     - A user-specified name for the cache parameter group.
     required: yes
     type: string
  description:
    description:
      - A user-specified description for the cache parameter group.
  state:
    description:
      - Idempotent actions that will create/modify, destroy, or reset a cache parameter group as needed.
    choices: ['present', 'absent', 'reset']
    required: true
  update_values:
    description:
      - A user-specified list of parameters to reset or modify for the cache parameter group.
    required: no
    type: list
    default: None
"""

EXAMPLES = """
# Note: None of these examples set aws_access_key, aws_secret_key, or region.
# It is assumed that their matching environment variables are set.
---
- hosts: localhost
  connection: local
  tasks:
    - name: 'Create a test parameter group'
      elasticache_parameter_group:
        name: 'test-param-group'
        group_family: 'redis3.2'
        description: 'This is a cache parameter group'
        state: 'present'
    - name: 'Modify a test parameter group'
      elasticache_parameter_group:
        name: 'test-param-group'
        update_values:
          - ['activerehashing', 'yes']
          - ['client-output-buffer-limit-normal-hard-limit', 4]
        state: 'present'
    - name: 'Reset all modifiable parameters for the test parameter group'
      elasticache_parameter_group:
        name: 'test-param-group'
        state: reset
    - name: 'Delete a test parameter group'
      elasticache_parameter_group:
        name: 'test-param-group'
        state: 'absent'

"""

from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

def create(conn, name, group_family, description):
    """ Create ElastiCache parameter group. """
    try:
        response = conn.create_cache_parameter_group(CacheParameterGroupName=name, CacheParameterGroupFamily=group_family, Description=description)
        changed = True
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.message)
    return response, changed
     
def delete(conn, name):
    """ Delete ElastiCache parameter group. """
    try:
        response = conn.delete_cache_parameter_group(CacheParameterGroupName=name)
        changed = True
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.message)
    return response, changed

def make_current_modifiable_param_dict(conn, name):
    """ Gets the current state of the cache parameter group and creates a dictionary with the format: {ParameterName: [Allowed_Values, DataType, ParameterValue]}"""
    current_info = get_info(conn, name)
    if current_info is False:
        return False
         
    parameters = current_info["Parameters"]
    modifiable_params = {}

    for param in parameters:
        if param["IsModifiable"] == True:
            if ("AllowedValues" and "ParameterValue") in param:
                modifiable_params[param["ParameterName"]] = [param["AllowedValues"], param["DataType"], param["ParameterValue"]]
    return modifiable_params

def check_valid_modification(module, update_values, modifiable_params):
    """ Check if the parameters and values in update_values are valid.  """
    changed_with_update = False

    for param_value_pair in update_values:
        parameter = param_value_pair[0]
        new_value = param_value_pair[1]
        
        # check valid modifiable parameters
        if parameter not in modifiable_params.keys():
            module.fail_json("%s is not a modifiable parameter. Valid parameters to modify are: %s." % (parameter, modifiable_params.keys()))
            
        # check allowed datatype for modified parameters
        str_to_type = {"integer": int, "string": str}
        if type(new_value) != str_to_type[modifiable_params[parameter][1]]:
            module.fail_json(msg="%s (type %s) is not an allowed value for the parameter %s. Expected a type %s." % (new_value, type(new_value), parameter, modifiable_params[parameter][1]))
        
        # check allowed values for modifiable parameters
        if str(new_value) not in modifiable_params[parameter][0]:
            if "-" not in modifiable_params[parameter][0]:
                module.fail_json(msg="%s is not an allowed value for the parameter %s. Valid parameters are: %s." % (value, modified, modifiable_params[parameter][0]))

        # check if a new value is different from current value
        if str(new_value) != modifiable_params[parameter][2]:
            changed_with_update = True

    return changed_with_update

def check_changed_parameter_values(update_values, old_parameters, new_parameters):
    """ Checking if the new values are different than the old values.  """
    changed_with_update = False

    # if the user specified parameters to reset, only check those for change
    if update_values:
        for param_value_pair in update_values:
            parameter = param_value_pair[0]
            if old_parameters[parameter] != new_parameters[parameter]:
                changed_with_update = True
                break
    # otherwise check all to find a change            
    else:
        for parameter in old_parameters.keys():
            if old_parameters[parameter] != new_parameters[parameter]:
                changed_with_update = True
                break
    
    return changed_with_update

def modify(conn, name, update_values):
    """ Modify ElastiCache parameter group to reflect the new information if it differs from the current. """
    # compares current group parameters with the parameters we've specified to to a value to see if this will change the group
    format_parameters = []
    for key_value_pair in update_values:
        key = key_value_pair[0]
        value = str(key_value_pair[1])
        format_parameters.append({'ParameterName': key, 'ParameterValue': value})
    try:
        response = conn.modify_cache_parameter_group(CacheParameterGroupName=name, ParameterNameValues=format_parameters)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.message)
    return response

def reset(conn, name, update_values):
    """ Reset ElastiCache parameter group if the current information is different from the new information. """
    # used to compare with the reset parameters' dict to see if there have been changes
    old_parameters_dict = make_current_modifiable_param_dict(conn, name)
    
    format_parameters = []
    
    # determine whether to reset all or specific parameters
    if update_values:
        all_parameters = False
        format_parameters = []
        for key_value_pair in update_values:
            key = key_value_pair[0]
            value = str(key_value_pair[1])
            format_parameters.append({'ParameterName': key, 'ParameterValue': value})
    else:
        all_parameters = True

    try:
        response = conn.reset_cache_parameter_group(CacheParameterGroupName=name, ParameterNameValues=format_parameters, ResetAllParameters=all_parameters)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg=e.message) 
        
    # determine changed
    new_parameters_dict = make_current_modifiable_param_dict(conn, name)
    changed = check_changed_parameter_values(update_values, old_parameters_dict, new_parameters_dict)
    
    return response, changed

def get_info(conn, name):
    """ Gets info about the ElastiCache parameter group. Returns false if it doesn't exist or we don't have access. """
    try:
        data = conn.describe_cache_parameters(CacheParameterGroupName=name)
        return data
    except botocore.exceptions.ClientError as e:
        return False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        group_family    = dict(required=False, type='str', choices=['memcached1.4', 'redis2.6', 'redis2.8', 'redis3.2']),
        name            = dict(required=True, type='str'),
        description     = dict(required=False),
        state           = dict(required=True),
        update_values   = dict(required=False, type='list'),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto required for this module')

    parameter_group_family  = module.params.get('group_family')
    parameter_group_name    = module.params.get('name')
    group_description       = module.params.get('description')
    state                   = module.params.get('state')
    update_values           = module.params.get('update_values')
    
    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg = str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region     or ec2_region must be set."))

    connection = boto3_conn(module, conn_type='client', 
                            resource='elasticache', region=region, 
                            endpoint=ec2_url, **aws_connect_kwargs)

    exists = get_info(connection, parameter_group_name)
     
    # check that the needed requirements are available
    if state == 'present' and exists and not update_values:
        module.fail_json(msg="Group already exists. Please specify values to modify using the 'update_values' option or use the state 'reset' if you want to reset all or some group parameters.")
    elif state == 'present' and update_values and not exists:
        module.fail_json(msg="No group to modify. Please create the cache parameter group before using the 'update_values' option.")
    elif state == 'present' and not exists and not (parameter_group_family or group_description):
        module.fail_json(msg="Creating a group requires a group name, the group family, and a description.")
    elif state == 'reset' and not exists:
        module.fail_json(msg="No group %s to reset. Please create the group before using the state 'reset'." % parameter_group_name)

    # Taking action
    changed = False
    if state == 'present':
        # modify existing group
        if exists:
            modifiable_params = make_current_modifiable_param_dict(connection, parameter_group_name)
            changed = check_valid_modification(module, update_values, modifiable_params)
            result = modify(connection, parameter_group_name, update_values)
        # create group
        else:
            result, changed = create(connection, parameter_group_name, parameter_group_family, group_description)
    elif state == 'absent':
        # delete group
        if exists:
            result, changed = delete(connection, parameter_group_name)
        else:
            changed = False
    elif state == 'reset':
        result, changed = reset(connection, parameter_group_name, update_values)

    facts_result = dict(changed=changed, elasticache=get_info(connection, parameter_group_name))

    module.exit_json(**facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
