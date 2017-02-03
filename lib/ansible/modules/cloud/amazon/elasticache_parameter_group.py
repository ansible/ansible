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

import traceback

try:
    import boto
    from boto.elasticache.layer1 import ElastiCacheConnection
    from boto.regioninfo import RegionInfo
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

class ElastiCacheManager(object):
    def __init__(self, module, aws_connect_kwargs, state, group_name, group_family, description, update_values, region):
        self.module = module
        self.aws_connect_kwargs = aws_connect_kwargs
        self.state = state
        self.name = group_name
        self.group_family = group_family
        self.description = description
        self.update_values = update_values

        self.changed = False
        self.response = None
        self.region = region
        self._get_elasticache_connection()
        self.exists = self.get_info()

    def _get_elasticache_connection(self):
        """Get an elasticache connection"""
        try:
            endpoint = "elasticache.%s.amazonaws.com" % self.region
            connect_region = RegionInfo(name=self.region, endpoint=endpoint)
            self.conn = ElastiCacheConnection(region=connect_region, **self.aws_connect_kwargs)
        except boto.exception.NoAuthHandlerFound as e:
            self.module.fail_json(msg=e.message)

    def create(self):
        """ Create ElastiCache parameter group if it doesn't exist. If it does exist, update it if needed. """
        try:
            self.response = self.conn.create_cache_parameter_group(cache_parameter_group_name=self.name, cache_parameter_group_family=self.group_family, description=self.description)
            self.changed = True
        except boto.exception.BotoServerError as e:
            self.module.fail_json(msg=e.message)
 
    def delete(self):
        """ Delete ElastiCache parameter group if it exists. """
        if self.exists:
            try:
                self.response = self.conn.delete_cache_parameter_group(cache_parameter_group_name=self.name)
                self.changed = True
            except boto.exception.BotoServerError as e:
                self.module.fail_json(msg=e.message)

    def make_current_modifiable_param_dict(self):
        """ Gets the current state of the cache parameter group and creates a dictionary with the format: {ParameterName: [Allowed_Values, DataType, ParameterValue]}"""
        current_info = self.get_info()
        if current_info is False:
            self.module.fail_json(msg="The the parameter group cannot be found. Ensure it exists and you have access to it.")
        
        parameters = current_info["DescribeCacheParametersResponse"]["DescribeCacheParametersResult"]["Parameters"]
        modifiable_params = {}

        for i in range(0, len(parameters)):
            param = parameters[i]
            if param["IsModifiable"] == True:
                modifiable_params[param["ParameterName"]] = [param["AllowedValues"], param["DataType"], param["ParameterValue"]]

        return modifiable_params

    def check_valid_parameter_names(self):
        """ Check if the parameters and values in update_values are valid.  """
        modifiable_params = self.make_current_modifiable_param_dict()
        
        if self.state == "reset":
            # returning the current parameter dict so we can compare it for changes after everything has been reset
            return modifiable_params

        changed_with_update = False

        for i in range(0, len(self.update_values)):
            # check valid modifiable parameters
            modified = self.update_values[i][0]
            if modified not in modifiable_params.keys():
                self.module.fail_json(msg="%s is not a modifiable parameter." % modified)

        changed_with_update = self.check_valid_parameter_name_values(modifiable_params, allowed_index=0, type_index=1, value_index=2)

        return changed_with_update

    def check_changed_parameter_values(self, old_parameters, new_parameters):
        """ Checking if the new values are different than the old values.  """
        changed_with_update = False

        # if the user specified parameters to reset, only check those for change
        if self.update_values:
            for i in range(0, len(self.update_values)):
                parameter = self.update_values[i][0]
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

    def check_valid_parameter_name_values(self, modifiable_params, allowed_index, type_index, value_index):
        """ Check if the parameters and values in update_values are valid.  """
        changed_with_update = False

        new_param = 0
        new_value = 1
        
        # iterating through the length of self.update_values; each index is a parameter,value pair the user wants to modify
        for i in range(0, len(self.update_values)):
            
            # check valid modifiable parameters
            modified = self.update_values[i][new_param]
            if modified not in modifiable_params.keys():
                self.module.fail_json("%s is not a modifiable parameter." % modified)
            
            # check allowed values for modifiable parameters
            value = self.update_values[i][new_value]
            if str(value) not in modifiable_params[modified][allowed_index]:
                if "-" not in modifiable_params[modified][allowed_index]:
                    self.module.fail_json(msg="%s is not an allowed value for the parameter %s. Valid parameters are: %s." % (value, modified, modifiable_params[modified][0]))

            # check allowed datatype for modifiable parameter values
            modified_type = type(self.update_values[i][new_value])
            expected_type = modifiable_params[modified][type_index]  # Out of index
            if (expected_type == "string" and modified_type != str) or (expected_type == "integer" and modified_type != int):
                self.module.fail_json(msg="%s (type %s) is not an allowed value for the parameter %s. Expected a type %s." % (value, modified_type, modified, expected_type))

            # check if a new value is different from current value; 1 value must be different for changed=True
            if str(value) != modifiable_params[modified][value_index]:
                changed_with_update = True
        
        return changed_with_update

    def modify(self):
        """ Modify ElastiCache parameter group to reflect the new information if it differs from the current. """
        # compares current group parameters with the parameters we've specified to to a value to see if this will change the group
        changed_with_update = self.check_valid_parameter_names()
        try:
            self.response = self.conn.modify_cache_parameter_group(cache_parameter_group_name=self.name, parameter_name_values=self.update_values)
            self.changed = changed_with_update
        except boto.exception.BotoServerError as e:
            self.module.fail_json(msg=e.message)

    def reset(self):
        """ Reset ElastiCache parameter group if the current information is different from the new information. """
        # used to compare with the reset parameters' dict to see if there have been changes
        old_parameters_dict = self.make_current_modifiable_param_dict()
        
        # determine whether to reset all or specific parameters
        if self.update_values:
            all_parameters = False
        else:
            all_parameters = True

        try:
            self.response = self.conn.reset_cache_parameter_group(cache_parameter_group_name=self.name, parameter_name_values=self.update_values, reset_all_parameters=all_parameters)
        except boto.exception.BotoServerError as e:
            self.module.fail_json(msg=e.message) 
        
        # determine self.changed
        new_parameters_dict = self.make_current_modifiable_param_dict()
        self.changed = self.check_changed_parameter_values(old_parameters_dict, new_parameters_dict)

    def get_info(self):
        """ Gets info about the ElastiCache parameter group. Returns false if it doesn't exist or we don't have access. """
        try:
            data = self.conn.describe_cache_parameters(cache_parameter_group_name=self.name)
            return data
        except boto.exception.BotoServerError:
            return False


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        group_family    = dict(required=False, type='str', choices=['memcached1.4', 'redis2.6', 'redis2.8', 'redis3.2']),
        name            = dict(required=True, type='str'),
        description     = dict(required=False),
        state           = dict(required=True),
        update_values   = dict(required=False, type='list', default=[]),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    req = { 'present'   : {'allow' : ['group_family', 'name', 'description'], 'not_allowed' : [] },
            'absent'    : {'allow' : [], 'not_allowed' : [] },
            'reset'     : {'allow' : [], 'not_allowed' : [] },
    }

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    parameter_group_family  = module.params.get('group_family')
    parameter_group_name    = module.params.get('name')
    group_description       = module.params.get('description')
    state                   = module.params.get('state')
    update_values           = module.params.get('update_values')
    
    # check legal parameters
    for requirement in req[state]['allow']:
        if not module.params.get(requirement):
            module.fail_json(msg="Option %s required for state=%s" % (requirement, state))
    for requirment in req[state]['not_allowed']:
        if module.params.get(requirement):
            module.fail_json(msg="Option %s not allowed for state:%s" % (requirement, state))

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg = str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    elasticache_manager = ElastiCacheManager(module, aws_connect_kwargs, state, parameter_group_name, parameter_group_family, group_description, update_values, region)
    exists = elasticache_manager.exists
    
    # check if modifications specified or not are valid
    if state == 'present' and exists and not update_values:
        module.fail_json(msg="Group already exists. Please specify values to modify using the 'update_values' option or use the state 'reset' if you want to reset all or some group parameters.")
    elif state == 'present' and update_values and not exists:
        module.fail_json(msg="No group to modify. Please create the cache parameter group before using the 'update_values' option.")
    elif state == 'reset' and not exists:
        module.fail_json(msg="No group %s to reset. Please create the group before using the state 'reset'." % parameter_group_name)

    if state == 'present':
        # modify existing group
        if exists:
            elasticache_manager.modify() 
        # create group
        else:
            elasticache_manager.create()
    elif state == 'absent':
        # delete group
        elasticache_manager.delete()
    elif state == 'reset':
        # reset group parameters
        elasticache_manager.reset()

    facts_result = dict(changed=elasticache_manager.changed, elasticache=elasticache_manager.get_info())

    module.exit_json(**facts_result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

if __name__ == '__main__':
    main()
