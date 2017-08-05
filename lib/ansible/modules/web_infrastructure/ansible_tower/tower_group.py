#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_group
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower group.
description:
    - Create, update, or destroy Ansible Tower groups. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the group.
      required: True
    description:
      description:
        - The description to use for the group.
      required: False
      default: null
    inventory:
      description:
        - Inventory the group should be made a member of.
      required: True
    variables:
      description:
        - Variables to use for the group, use '@' for a file.
      required: False
      default: null
    credential:
      description:
        - Credential to use for the group.
      required: False
      default: null
    source:
      description:
        - The source to use for this group.
      required: False
      default: null,
      choices: ["manual", "file", "ec2", "rax", "vmware", "gce", "azure", "azure_rm", "openstack", "satellite6" , "cloudforms", "custom"]
    source_regions:
      description:
        - Regions for cloud provider.
      required: False
      default: null
    source_vars:
      description:
        - Override variables from source with variables from this field.
      required: False
      default: null
    instance_filters:
      description:
        - Comma-separated list of filter expressions for matching hosts.
      required: False
      default: null
    group_by:
      description:
        - Limit groups automatically created from inventory source.
      required: False
      default: null
    source_script:
      description:
        - Inventory script to be used when group type is "custom".
      required: False
      default: null
    overwrite:
      description:
        - Delete child roups and hosts not found in source.
      required: False
      default: False
    overwrite_vars:
      description:
        - Override vars in child groups and hosts with those from external source.
      required: False
      default: null
    update_on_launch:
      description:
        - Refresh inventory data from its source each time a job is run.
      required: False
      default: False
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
    tower_host:
      description:
        - URL to your Tower instance.
      required: False
      default: null
    tower_username:
        description:
          - Username for your Tower instance.
        required: False
        default: null
    tower_password:
        description:
          - Password for your Tower instance.
        required: False
        default: null
    tower_verify_ssl:
        description:
          - Dis/allow insecure connections to Tower. If C(no), SSL certificates will not be validated.
            This should only be used on personally controlled sites using self-signed certificates.
        required: False
        default: True
    tower_config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "python >= 2.6"
  - "ansible-tower-cli >= 3.0.2"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
- name: Add tower group
  tower_group:
    name: localhost
    description: "Local Host Group"
    inventory: "Local Inventory"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''


try:
    import os
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
    from ansible.module_utils.ansible_tower import tower_auth_config, tower_check_mode

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            description=dict(),
            inventory=dict(required=True),
            variables=dict(),
            credential=dict(),
            source=dict(choices=["manual", "file", "ec2", "rax", "vmware",
                                 "gce", "azure", "azure_rm", "openstack",
                                 "satellite6", "cloudforms", "custom"], default="manual"),
            source_regions=dict(),
            source_vars=dict(),
            instance_filters=dict(),
            group_by=dict(),
            source_script=dict(),
            overwrite=dict(type='bool', default=False),
            overwrite_vars=dict(),
            update_on_launch=dict(type='bool', default=False),
            tower_host=dict(),
            tower_username=dict(),
            tower_password=dict(no_log=True),
            tower_verify_ssl=dict(type='bool', default=True),
            tower_config_file=dict(type='path'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    inventory = module.params.get('inventory')
    credential = module.params.get('credential')
    state = module.params.get('state')

    variables = module.params.get('variables')
    if variables:
        if variables.startswith('@'):
            filename = os.path.expanduser(variables[1:])
            variables = module.contents_from_file(filename)

    json_output = {'group': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        group = tower_cli.get_resource('group')
        try:
            params = module.params.copy()
            params['create_on_missing'] = True
            params['variables'] = variables

            inv_res = tower_cli.get_resource('inventory')
            inv = inv_res.get(name=inventory)
            params['inventory'] = inv['id']

            if credential:
                cred_res = tower_cli.get_resource('credential')
                cred = cred_res.get(name=credential)
                params['credential'] = cred['id']

            if state == 'present':
                result = group.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = group.delete(**params)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group, inventory not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update the group: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
