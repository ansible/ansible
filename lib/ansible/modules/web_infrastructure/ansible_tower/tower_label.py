#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_label
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower label.
description:
    - Create, update, or destroy Ansible Tower labels. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the label.
      required: True
    organization:
      description:
        - Organization the label should be applied to.
      required: True
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add label to tower organization
  tower_label:
    name: Custom Label
    organization: My Organization
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ansible.module_utils.ansible_tower import tower_argument_spec, tower_auth_config, tower_check_mode, HAS_TOWER_CLI

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = tower_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        organization=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    organization = module.params.get('organization')
    state = module.params.get('state')

    json_output = {'label': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        label = tower_cli.get_resource('label')

        try:
            org_res = tower_cli.get_resource('organization')
            org = org_res.get(name=organization)

            if state == 'present':
                result = label.modify(name=name, organization=org['id'], create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = label.delete(name=name, organization=org['id'])
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update label, organization not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update label: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
