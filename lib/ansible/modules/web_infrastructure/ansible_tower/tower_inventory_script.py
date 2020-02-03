#!/usr/bin/python
# coding: utf-8 -*-

# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}


DOCUMENTATION = '''
---
module: tower_inventory_script
author: "Adrien Fleury (@fleu42)"
version_added: "2.10"
short_description: create, update, or destroy Ansible Tower inventory scripts.
description:
    - Create, update, or destroy Ansible Tower inventories scripts. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the inventory script.
      required: True
      type: str
    description:
      description:
        - The description to use for the inventory script.
      type: str
    organization:
      description:
        - Organization the inventory belongs to.
      required: True
      type: str
    timeout:
      description:
        - Number in seconds after which the Tower API methods will time out.
      type: int
    script:
      description:
        - Custom ansible script.
      required: True
      type: str
    state:
      description:
        - Desired state of the resource.
      default: "present"
      type: str
      choices: ["present", "absent"]
    validate_certs:
      description:
        - Tower option to avoid certificates check.
      type: bool
      aliases: [ tower_verify_ssl ]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add tower inventory script
  tower_inventory_script:
    name: inventory script
    description: My inventory script
    organization: My organisation
    script: "{{ lookup('template', './some_template.j2') }}"
'''


RETURN = ''' # '''


from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(required=False),
        organization=dict(required=True),
        script=dict(type='str', required=True),
        state=dict(choices=['present', 'absent'], default='present'),
        timeout=dict(type='int', required=False),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

    name = module.params.get('name')
    organization = module.params.get('organization')
    script = module.params.get('script')
    state = module.params.get('state')

    json_output = {'inventory_script': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        inventory_script = tower_cli.get_resource('inventory_script')
        try:
            params = {}
            params['name'] = name
            params['script'] = script

            if module.params.get('description'):
                params['description'] = module.params.get('description')

            try:
                org_res = tower_cli.get_resource('organization')
                org = org_res.get(name=organization)
                params['organization'] = org['id']
            except (exc.NotFound) as excinfo:
                module.fail_json(msg='Failed to update inventory script, organization not found: {0}'.format(excinfo), changed=False)

            for key in ('timeout'):
                if module.params.get(key) is not None:
                    params[key] = module.params.get(key)

            if state == 'present':
                params['create_on_missing'] = True
                result = inventory_script.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                params['fail_on_missing'] = False
                result = inventory_script.delete(**params)

        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update inventory script: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
