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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rds_param_group
version_added: "1.5"
short_description: manage RDS parameter groups
description:
     - Creates, modifies, and deletes RDS parameter groups. This module has a dependency on python-boto >= 2.5.
options:
  state:
    description:
      - Specifies whether the group should be present or absent.
    required: true
    default: present
    aliases: []
    choices: [ 'present' , 'absent' ]
  name:
    description:
      - Database parameter group identifier.
    required: true
    default: null
    aliases: []
  description:
    description:
      - Database parameter group description. Only set when a new group is added.
    required: false
    default: null
    aliases: []
  engine:
    description:
      - The type of database for this group. Required for state=present.
    required: false
    default: null
    aliases: []
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
    required: false
    default: null
    aliases: []
  params:
    description:
      - Map of parameter names and values. Numeric values may be represented as K for kilo (1024), M for mega (1024^2), G for giga (1024^3),
        or T for tera (1024^4), and these values will be expanded into the appropriate number before being set in the parameter group.
    required: false
    default: null
    aliases: []
author: "Scott Anderson (@tastychutney)"
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

# Remove a parameter group
- rds_param_group:
      state: absent
      name: norwegian_blue
'''

try:
    import boto.rds
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info
from ansible.module_utils.parsing.convert_bool import BOOLEANS_TRUE
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native


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


# returns a tuple: (whether or not a parameter was changed, the remaining parameters that weren't found in this parameter group)

class NotModifiableError(Exception):
    def __init__(self, error_message, *args):
        super(NotModifiableError, self).__init__(error_message, *args)
        self.error_message = error_message

    def __repr__(self):
        return 'NotModifiableError: %s' % self.error_message

    def __str__(self):
        return 'NotModifiableError: %s' % self.error_message


def set_parameter(param, value, immediate):
    """
    Allows setting parameters with 10M = 10* 1024 * 1024 and so on.
    """
    converted_value = value

    if param.type == 'string':
        converted_value = str(value)

    elif param.type == 'integer':
        if isinstance(value, string_types):
            try:
                for modifier in INT_MODIFIERS.keys():
                    if value.endswith(modifier):
                        converted_value = int(value[:-1]) * INT_MODIFIERS[modifier]
                converted_value = int(converted_value)
            except ValueError:
                # may be based on a variable (ie. {foo*3/4}) so
                # just pass it on through to boto
                converted_value = str(value)
        elif isinstance(value, bool):
            converted_value = 1 if value else 0
        else:
            converted_value = int(value)

    elif param.type == 'boolean':
        if isinstance(value, string_types):
            converted_value = to_native(value) in BOOLEANS_TRUE
        else:
            converted_value = bool(value)

    param.value = converted_value
    param.apply(immediate)

def modify_group(group, params, immediate=False):
    """ Set all of the params in a group to the provided new params. Raises NotModifiableError if any of the
        params to be changed are read only.
    """
    changed = {}

    new_params = dict(params)

    for key in new_params.keys():
        if key in group:
            param = group[key]
            new_value = new_params[key]

            try:
                old_value = param.value
            except ValueError:
                # some versions of boto have problems with retrieving
                # integer values from params that may have their value
                # based on a variable (ie. {foo*3/4}), so grab it in a
                # way that bypasses the property functions
                old_value = param._value

            if old_value != new_value:
                if not param.is_modifiable:
                    raise NotModifiableError('Parameter %s is not modifiable.' % key)

                changed[key] = {'old': old_value, 'new': new_value}

                set_parameter(param, new_value, immediate)

                del new_params[key]

    return changed, new_params


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state             = dict(required=True,  choices=['present', 'absent']),
        name              = dict(required=True),
        engine            = dict(required=False, choices=VALID_ENGINES),
        description       = dict(required=False),
        params            = dict(required=False, aliases=['parameters'], type='dict'),
        immediate         = dict(required=False, type='bool'),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state                   = module.params.get('state')
    group_name              = module.params.get('name').lower()
    group_engine            = module.params.get('engine')
    group_description       = module.params.get('description')
    group_params            = module.params.get('params') or {}
    immediate               = module.params.get('immediate') or False

    if state == 'present':
        for required in ['name', 'description', 'engine']:
            if not module.params.get(required):
                module.fail_json(msg = str("Parameter %s required for state='present'" % required))
    else:
        for not_allowed in ['description', 'engine', 'params']:
            if module.params.get(not_allowed):
                module.fail_json(msg = str("Parameter %s not allowed for state='absent'" % not_allowed))

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg = str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    try:
        conn = connect_to_aws(boto.rds, region, **aws_connect_kwargs)
    except boto.exception.BotoServerError as e:
        module.fail_json(msg = e.error_message)

    group_was_added = False

    try:
        changed = False

        try:
            all_groups = conn.get_all_dbparameter_groups(group_name, max_records=100)
            exists = len(all_groups) > 0
        except BotoServerError as e:
            if e.error_code != 'DBParameterGroupNotFound':
                module.fail_json(msg = e.error_message)
            exists = False

        if state == 'absent':
            if exists:
                conn.delete_parameter_group(group_name)
                changed = True
        else:
            changed = {}
            if not exists:
                new_group = conn.create_parameter_group(group_name, engine=group_engine, description=group_description)
                group_was_added = True

            # If a "Marker" is present, this group has more attributes remaining to check. Get the next batch, but only
            # if there are parameters left to set.
            marker = None
            while len(group_params):
                next_group = conn.get_all_dbparameters(group_name, marker=marker)

                changed_params, group_params = modify_group(next_group, group_params, immediate)
                changed.update(changed_params)

                if hasattr(next_group, 'Marker'):
                    marker = next_group.Marker
                else:
                    break

    except BotoServerError as e:
        module.fail_json(msg = e.error_message)

    except NotModifiableError as e:
        msg = e.error_message
        if group_was_added:
            msg = '%s The group "%s" was added first.' % (msg, group_name)
        module.fail_json(msg=msg)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()

