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
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rds_param_group
version_added: "1.5"
short_description: manage RDS parameter groups
description:
     - Creates, modifies, and deletes RDS parameter groups. This module has a dependency on python-boto >= 2.5.
requirements: [ boto3 ]
options:
  state:
    description:
      - Specifies whether the group should be present or absent.
    required: true
    default: present
    choices: [ 'present' , 'absent' ]
  name:
    description:
      - Database parameter group identifier.
    required: true
  description:
    description:
      - Database parameter group description. Only set when a new group is added.
  engine:
    description:
      - The type of database for this group. Required for state=present.
    choices:
        - 'aurora5.6'
        - 'mariadb10.0'
        - 'mariadb10.1'
        - 'mysql5.1'
        - 'mysql5.5'
        - 'mysql5.6'
        - 'mysql5.7'
        - 'oracle-ee-11.2'
        - 'oracle-ee-12.1'
        - 'oracle-se-11.2'
        - 'oracle-se-12.1'
        - 'oracle-se1-11.2'
        - 'oracle-se1-12.1'
        - 'postgres9.3'
        - 'postgres9.4'
        - 'postgres9.5'
        - 'postgres9.6'
        - 'sqlserver-ee-10.5'
        - 'sqlserver-ee-11.0'
        - 'sqlserver-ex-10.5'
        - 'sqlserver-ex-11.0'
        - 'sqlserver-ex-12.0'
        - 'sqlserver-se-10.5'
        - 'sqlserver-se-11.0'
        - 'sqlserver-se-12.0'
        - 'sqlserver-web-10.5'
        - 'sqlserver-web-11.0'
        - 'sqlserver-web-12.0'
  immediate:
    description:
      - Whether to apply the changes immediately, or after the next reboot of any associated instances.
    aliases:
      - apply_immediately
  params:
    description:
      - Map of parameter names and values. Numeric values may be represented as K for kilo (1024), M for mega (1024^2), G for giga (1024^3),
        or T for tera (1024^4), and these values will be expanded into the appropriate number before being set in the parameter group.
    aliases: [parameters]
  tags:
    description:
      - Dictionary of tags to attach to the parameter group
    version_added: "2.4"
  purge_tags:
    description:
      - Whether or not to remove tags that do not appear in the I(tags) list. Defaults to false.
    version_added: "2.4"
author:
    - "Scott Anderson (@tastychutney)"
    - "Will Thames (@willthames)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Add or change a parameter group, in this case setting auto_increment_increment to 42 * 1024
- rds_param_group:
      state: present
      name: norwegian_blue
      description: 'My Fancy Ex Parrot Group'
      engine: 'mysql5.6'
      params:
          auto_increment_increment: "42K"
      tags:
          Environment: production
          Application: parrot

# Remove a parameter group
- rds_param_group:
      state: absent
      name: norwegian_blue
'''

RETURN = '''
db_parameter_group_name:
    description: Name of DB parameter group
    type: string
    returned: when state is present
db_parameter_group_family:
    description: DB parameter group family that this DB parameter group is compatible with.
    type: string
    returned: when state is present
db_parameter_group_arn:
    description: ARN of the DB parameter group
    type: string
    returned: when state is present
description:
    description: description of the DB parameter group
    type: string
    returned: when state is present
errors:
    description: list of errors from attempting to modify parameters that are not modifiable
    type: list
    returned: when state is present
tags:
    description: dictionary of tags
    type: dict
    returned: when state is present
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import ec2_argument_spec, get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, HAS_BOTO3, compare_aws_tags
from ansible.module_utils.ec2 import ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native

import traceback

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


VALID_ENGINES = [
    'aurora5.6',
    'mariadb10.0',
    'mariadb10.1',
    'mysql5.1',
    'mysql5.5',
    'mysql5.6',
    'mysql5.7',
    'oracle-ee-11.2',
    'oracle-ee-12.1',
    'oracle-se-11.2',
    'oracle-se-12.1',
    'oracle-se1-11.2',
    'oracle-se1-12.1',
    'postgres9.3',
    'postgres9.4',
    'postgres9.5',
    'postgres9.6',
    'sqlserver-ee-10.5',
    'sqlserver-ee-11.0',
    'sqlserver-ex-10.5',
    'sqlserver-ex-11.0',
    'sqlserver-ex-12.0',
    'sqlserver-se-10.5',
    'sqlserver-se-11.0',
    'sqlserver-se-12.0',
    'sqlserver-web-10.5',
    'sqlserver-web-11.0',
    'sqlserver-web-12.0',
]

INT_MODIFIERS = {
    'K': 1024,
    'M': pow(1024, 2),
    'G': pow(1024, 3),
    'T': pow(1024, 4),
}


def convert_parameter(param, value):
    """
    Allows setting parameters with 10M = 10* 1024 * 1024 and so on.
    """
    converted_value = value

    if param['DataType'] == 'integer':
        if isinstance(value, string_types):
            try:
                for modifier in INT_MODIFIERS.keys():
                    if value.endswith(modifier):
                        converted_value = int(value[:-1]) * INT_MODIFIERS[modifier]
            except ValueError:
                # may be based on a variable (ie. {foo*3/4}) so
                # just pass it on through to boto
                pass
        elif isinstance(value, bool):
            converted_value = 1 if value else 0

    elif param['DataType'] == 'boolean':
        if isinstance(value, string_types):
            converted_value = to_native(value) in BOOLEANS_TRUE
        # convert True/False to 1/0
        converted_value = 1 if converted_value else 0
    return str(converted_value)


def update_parameters(module, connection):
    groupname = module.params['name']
    desired = module.params['params']
    apply_method = 'immediate' if module.params['immediate'] else 'pending-reboot'
    errors = []
    modify_list = []
    parameters_paginator = connection.get_paginator('describe_db_parameters')
    existing = parameters_paginator.paginate(DBParameterGroupName=groupname).build_full_result()['Parameters']
    lookup = dict((param['ParameterName'], param) for param in existing)
    for param_key, param_value in desired.items():
        if param_key not in lookup:
            errors.append("Parameter %s is not an available parameter for the %s engine" %
                          (param_key, module.params.get('engine')))
        else:
            converted_value = convert_parameter(lookup[param_key], param_value)
            # engine-default parameters do not have a ParameterValue, so we'll always override those.
            if converted_value != lookup[param_key].get('ParameterValue'):
                if lookup[param_key]['IsModifiable']:
                    modify_list.append(dict(ParameterValue=converted_value, ParameterName=param_key, ApplyMethod=apply_method))
                else:
                    errors.append("Parameter %s is not modifiable" % param_key)

    # modify_db_parameters takes at most 20 parameters
    if modify_list:
        try:
            from itertools import izip_longest as zip_longest  # python 2
        except ImportError:
            from itertools import zip_longest  # python 3
        for modify_slice in zip_longest(*[iter(modify_list)] * 20, fillvalue=None):
            non_empty_slice = [item for item in modify_slice if item]
            try:
                connection.modify_db_parameter_group(DBParameterGroupName=groupname, Parameters=non_empty_slice)
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Couldn't update parameters: %s" % str(e),
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
        return True, errors
    return False, errors


def update_tags(module, connection, group, tags):
    changed = False
    existing_tags = connection.list_tags_for_resource(ResourceName=group['DBParameterGroupArn'])['TagList']
    to_update, to_delete = compare_aws_tags(boto3_tag_list_to_ansible_dict(existing_tags),
                                            tags, module.params['purge_tags'])
    if to_update:
        try:
            connection.add_tags_to_resource(ResourceName=group['DBParameterGroupArn'],
                                            Tags=ansible_dict_to_boto3_tag_list(to_update))
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't add tags to parameter group: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        except botocore.exceptions.ParamValidationError as e:
            # Usually a tag value has been passed as an int or bool, needs to be a string
            # The AWS exception message is reasonably ok for this purpose
            module.fail_json(msg="Couldn't add tags to parameter group: %s." % str(e),
                             exception=traceback.format_exc())
    if to_delete:
        try:
            connection.remove_tags_from_resource(ResourceName=group['DBParameterGroupArn'],
                                                 TagKeys=to_delete)
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't remove tags from parameter group: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    return changed


def ensure_present(module, connection):
    groupname = module.params['name']
    tags = module.params.get('tags')
    changed = False
    errors = []
    try:
        response = connection.describe_db_parameter_groups(DBParameterGroupName=groupname)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBParameterGroupNotFound':
            response = None
        else:
            module.fail_json(msg="Couldn't access parameter group information: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    if not response:
        params = dict(DBParameterGroupName=groupname,
                      DBParameterGroupFamily=module.params['engine'],
                      Description=module.params['description'])
        if tags:
            params['Tags'] = ansible_dict_to_boto3_tag_list(tags)
        try:
            response = connection.create_db_parameter_group(**params)
            changed = True
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't create parameter group: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    else:
        group = response['DBParameterGroups'][0]
        if tags:
            changed = update_tags(module, connection, group, tags)

    if module.params.get('params'):
        params_changed, errors = update_parameters(module, connection)
        changed = changed or params_changed

    try:
        response = connection.describe_db_parameter_groups(DBParameterGroupName=groupname)
        group = camel_dict_to_snake_dict(response['DBParameterGroups'][0])
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't obtain parameter group information: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    try:
        tags = connection.list_tags_for_resource(ResourceName=group['db_parameter_group_arn'])['TagList']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't obtain parameter group tags: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    group['tags'] = boto3_tag_list_to_ansible_dict(tags)

    module.exit_json(changed=changed, errors=errors, **group)


def ensure_absent(module, connection):
    group = module.params['name']
    try:
        response = connection.describe_db_parameter_groups(DBParameterGroupName=group)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBParameterGroupNotFound':
            module.exit_json(changed=False)
        else:
            module.fail_json(msg="Couldn't access parameter group information: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    try:
        response = connection.delete_db_parameter_group(DBParameterGroupName=group)
        module.exit_json(changed=True)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't delete parameter group: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            state=dict(required=True, choices=['present', 'absent']),
            name=dict(required=True),
            engine=dict(),
            description=dict(),
            params=dict(aliases=['parameters'], type='dict'),
            immediate=dict(type='bool', aliases=['apply_immediately']),
            tags=dict(type='dict', default={}),
            purge_tags=dict(type='bool', default=False)
        )
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[['state', 'present', ['description', 'engine']]])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 and botocore are required for this module')

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)

    if not region:
        module.fail_json(msg="Region must be present")

    try:
        conn = boto3_conn(module, conn_type='client', resource='rds', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg="Couldn't connect to AWS: %s" % str(e))

    state = module.params.get('state')
    if state == 'present':
        ensure_present(module, conn)
    if state == 'absent':
        ensure_absent(module, conn)


if __name__ == '__main__':
    main()
