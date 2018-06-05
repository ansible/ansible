#!/usr/bin/python
# coding: utf-8 -*-
#
# (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_inventory_source
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: create, update, or destroy Ansible Tower inventory source.
description:
    - Create, update, or destroy Ansible Tower inventories source. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory source.
      required: True
    description:
      description:
        - The description to use for the inventory source.
      required: False
      default: null
    inventory:
      description:
        - The inventory the source is linked to.
      required: True
    source:
      description:
        - Types of inventory source.
      choices:
        - file
        - scm
        - ec2
        - gce
        - azure
        - azure_rm
        - vmware
        - satellite6
        - cloudforms
        - openstack
        - rhv
        - tower
        - custom
      required: True
    credential:
      description:
        - Credential to use to retrieve the inventory from.
      required: False
    source_vars:
      description:
        - >-
          The source_vars allow to Override variables found in the source config
          file. For example with Openstack, specifying *private: false* would
          change the output of the openstack.py script. It has to be YAML or
          JSON.
      required: False
    timeout:
      description:
        - Number in seconds after which the Tower API methods will time out.
    source_project:
      description:
        - Use a *project* as a source for the *inventory*.
      required: False
    source_path:
      description:
        - Path to the file to use as a source in the selected *project*.
      required: False
    update_on_project_update:
      description:
        - >-
          That parameter will sync the inventory when the project is synced. It
          can only be used with a SCM source.
      required: False
      type: bool
    source_regions:
      description:
        - >-
          List of regions for your cloud provider. You can include multiple all
          regions. Only Hosts associated with the selected regions will be
          updated. Refer to Ansible Tower documentation for more detail.
      required: False
    instance_filters:
      description:
        - >-
          Provide a comma-separated list of filter expressions. Hosts are
          imported when all of the filters match. Refer to Ansible Tower
          documentation for more detail.
      required: False
    group_by:
      description:
        - >-
          Specify which groups to create automatically. Group names will be
          created similar to the options selected. If blank, all groups above
          are created. Refer to Ansible Tower documentation for more detail.
      required: False
    source_script:
      description:
        - >-
          The source custom script to use to build the inventory. It needs to
          exist.
      required: False
    overwrite:
      description:
        - >-
          If set, any hosts and groups that were previously present on the
          external source but are now removed will be removed from the Tower
          inventory. Hosts and groups that were not managed by the inventory
          source will be promoted to the next manually created group or if
          there is no manually created group to promote them into, they will be
          left in the "all" default group for the inventory. When not checked,
          local child hosts and groups not found on the external source will
          remain untouched by the inventory update process.
      required: False
      type: bool
    overwrite_vars:
      description:
        - >-
          If set, all variables for child groups and hosts will be removed
          and replaced by those found on the external source. When not checked,
          a merge will be performed, combining local variables with those found
          on the external source.
      required: False
      type: bool
    update_on_launch:
      description:
        - >-
          Each time a job runs using this inventory, refresh the inventory from
          the selected source before executing job tasks.
      required: False
      type: bool
    update_cache_timeout:
      description:
        - >-
          Time in seconds to consider an inventory sync to be current. During
          job runs and callbacks the task system will evaluate the timestamp of
          the latest sync. If it is older than Cache Timeout, it is not
          considered current, and a new inventory sync will be performed.
      required: False
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
    tower_verify_ssl:
      description:
        - Tower option to avoid certificates check.
      required: False
      type: bool
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add tower inventory source
  tower_inventory_source:
    name: Inventory source
    description: My Inventory source
    inventory: My inventory
    credential: Devstack_credential
    source: openstack
    update_on_launch: true
    overwrite: true
    source_vars: '{ private: false }'
    state: present
    tower_verify_ssl: false
'''


RETURN = ''' # '''


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_tower import (
    tower_argument_spec,
    tower_auth_config,
    tower_check_mode,
    HAS_TOWER_CLI
)

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


SOURCE_CHOICES = {
    'file': 'Directory or Script',
    'scm': 'Sourced from a Project',
    'ec2': 'Amazon EC2',
    'gce': 'Google Compute Engine',
    'azure': 'Microsoft Azure',
    'azure_rm': 'Microsoft Azure Resource Manager',
    'vmware': 'VMware vCenter',
    'satellite6': 'Red Hat Satellite 6',
    'cloudforms': 'Red Hat CloudForms',
    'openstack': 'OpenStack',
    'rhv': 'Red Hat Virtualization',
    'tower': 'Ansible Tower',
    'custom': 'Custom Script',
}


def main():
    argument_spec = tower_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        description=dict(required=False),
        inventory=dict(required=True),
        source=dict(required=True,
                    choices=SOURCE_CHOICES.keys()),
        credential=dict(required=False),
        source_vars=dict(required=False),
        timeout=dict(type='int', required=False),
        source_project=dict(required=False),
        source_path=dict(required=False),
        update_on_project_update=dict(type='bool', required=False),
        source_regions=dict(required=False),
        instance_filters=dict(required=False),
        group_by=dict(required=False),
        source_script=dict(required=False),
        overwrite=dict(type='bool', required=False),
        overwrite_vars=dict(type='bool', required=False),
        update_on_launch=dict(type='bool', required=False),
        update_cache_timeout=dict(type='int', required=False),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    inventory = module.params.get('inventory')
    source = module.params.get('source')
    state = module.params.get('state')

    json_output = {'inventory_source': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        inventory_source = tower_cli.get_resource('inventory_source')
        try:
            params = {}
            params['name'] = name
            params['source'] = source

            if module.params.get('description'):
                params['description'] = module.params.get('description')

            if module.params.get('credential'):
                credential_res = tower_cli.get_resource('credential')
                try:
                    credential = credential_res.get(
                        name=module.params.get('credential'))
                    params['credential'] = credential['id']
                except (exc.NotFound) as excinfo:
                    module.fail_json(
                        msg='Failed to update credential source,'
                        'credential not found: {0}'.format(excinfo),
                        changed=False
                    )

            if module.params.get('source_project'):
                source_project_res = tower_cli.get_resource('project')
                try:
                    source_project = source_project_res.get(
                        name=module.params.get('source_project'))
                    params['source_project'] = source_project['id']
                except (exc.NotFound) as excinfo:
                    module.fail_json(
                        msg='Failed to update source project,'
                        'project not found: {0}'.format(excinfo),
                        changed=False
                    )

            if module.params.get('source_script'):
                source_script_res = tower_cli.get_resource('inventory_script')
                try:
                    script = source_script_res.get(
                        name=module.params.get('source_script'))
                    params['source_script'] = script['id']
                except (exc.NotFound) as excinfo:
                    module.fail_json(
                        msg='Failed to update source script,'
                        'script not found: {0}'.format(excinfo),
                        changed=False
                    )

            try:
                inventory_res = tower_cli.get_resource('inventory')
                params['inventory'] = inventory_res.get(name=inventory)['id']
            except (exc.NotFound) as excinfo:
                module.fail_json(
                    msg='Failed to update inventory source, '
                    'inventory not found: {0}'.format(excinfo),
                    changed=False
                )

            for key in ('source_vars', 'timeout', 'source_path',
                        'update_on_project_update', 'source_regions',
                        'instance_filters', 'group_by', 'overwrite',
                        'overwrite_vars', 'update_on_launch',
                        'update_cache_timeout'):
                if module.params.get(key):
                    params[key] = module.params.get(key)

            if state == 'present':
                params['create_on_missing'] = True
                result = inventory_source.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                params['fail_on_missing'] = False
                result = inventory_source.delete(**params)

        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to update inventory source: \
                    {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
