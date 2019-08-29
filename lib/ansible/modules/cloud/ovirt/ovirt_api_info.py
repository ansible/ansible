#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: ovirt_api_info
short_description: Retrieve information about the oVirt/RHV API
author: "Ondra Machacek (@machacekondra)"
version_added: "2.5"
description:
    - "Retrieve information about the oVirt/RHV API."
    - This module was called C(ovirt_api_facts) before Ansible 2.9, returning C(ansible_facts).
      Note that the M(ovirt_api_info) module no longer returns C(ansible_facts)!
notes:
    - "This module returns a variable C(ovirt_api),
       which contains a information about oVirt/RHV API. You need to register the result with
       the I(register) keyword to use it."
extends_documentation_fragment: ovirt_info
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather information oVirt API:
- ovirt_api_info:
  register: result
- debug:
    msg: "{{ result.ovirt_api }}"
'''

RETURN = '''
ovirt_api:
    description: "Dictionary describing the oVirt API information.
                  Api attributes are mapped to dictionary keys,
                  all API attributes can be found at following
                  url: https://ovirt.example.com/ovirt-engine/api/model#types/api."
    returned: On success.
    type: dict
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_info_full_argument_spec,
)


def main():
    argument_spec = ovirt_info_full_argument_spec()
    module = AnsibleModule(argument_spec)
    is_old_facts = module._name == 'ovirt_api_facts'
    if is_old_facts:
        module.deprecate("The 'ovirt_api_facts' module has been renamed to 'ovirt_api_info', "
                         "and the renamed one no longer returns ansible_facts", version='2.13')
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        api = connection.system_service().get()
        result = dict(
            ovirt_api=get_dict_of_struct(
                struct=api,
                connection=connection,
                fetch_nested=module.params.get('fetch_nested'),
                attributes=module.params.get('nested_attributes'),
            )
        )
        if is_old_facts:
            module.exit_json(changed=False, ansible_facts=result)
        else:
            module.exit_json(changed=False, **result)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
