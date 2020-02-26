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
module: tower_credential_type
author: "Adrien Fleury (@fleu42)"
version_added: "2.7"
short_description: Create, update, or destroy custom Ansible Tower credential type.
description:
    - Create, update, or destroy Ansible Tower credential type. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name of the credential type.
      required: True
    description:
      description:
        - The description of the credential type to give more detail about it.
      required: False
    kind:
      description:
        - >-
          The type of credential type being added. Note that only cloud and
          net can be used for creating credential types. Refer to the Ansible
          for more information.
      choices: [ 'ssh', 'vault', 'net', 'scm', 'cloud', 'insights' ]
      required: False
    inputs:
      description:
        - >-
          Enter inputs using either JSON or YAML syntax. Refer to the Ansible
          Tower documentation for example syntax.
      required: False
    injectors:
      description:
        - >-
          Enter injectors using either JSON or YAML syntax. Refer to the
          Ansible Tower documentation for example syntax.
      required: False
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
    validate_certs:
      description:
        - Tower option to avoid certificates check.
      required: False
      type: bool
      aliases: [ tower_verify_ssl ]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- tower_credential_type:
    name: Nexus
    description: Credentials type for Nexus
    kind: cloud
    inputs: "{{ lookup('file', 'tower_credential_inputs_nexus.json') }}"
    injectors: {'extra_vars': {'nexus_credential': 'test' }}
    state: present
    validate_certs: false

- tower_credential_type:
    name: Nexus
    state: absent
'''


RETURN = ''' # '''


from ansible.module_utils.ansible_tower import (
    TowerModule,
    tower_auth_config,
    tower_check_mode
)

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


KIND_CHOICES = {
    'ssh': 'Machine',
    'vault': 'Ansible Vault',
    'net': 'Network',
    'scm': 'Source Control',
    'cloud': 'Lots of others',
    'insights': 'Insights'
}


def main():
    argument_spec = dict(
        name=dict(required=True),
        description=dict(required=False),
        kind=dict(required=False, choices=KIND_CHOICES.keys()),
        inputs=dict(type='dict', required=False),
        injectors=dict(type='dict', required=False),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    name = module.params.get('name')
    kind = module.params.get('kind')
    state = module.params.get('state')

    json_output = {'credential_type': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        credential_type_res = tower_cli.get_resource('credential_type')

        params = {}
        params['name'] = name
        params['kind'] = kind
        params['managed_by_tower'] = False

        if module.params.get('description'):
            params['description'] = module.params.get('description')

        if module.params.get('inputs'):
            params['inputs'] = module.params.get('inputs')

        if module.params.get('injectors'):
            params['injectors'] = module.params.get('injectors')

        try:
            if state == 'present':
                params['create_on_missing'] = True
                result = credential_type_res.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                params['fail_on_missing'] = False
                result = credential_type_res.delete(**params)

        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(
                msg='Failed to update credential type: {0}'.format(excinfo),
                changed=False
            )

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
