#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
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
#

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_full_argument_spec,
)


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ovirt_vmpools_facts
short_description: Retrieve facts about one or more oVirt vmpools
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt vmpools."
notes:
    - "This module creates a new top-level C(ovirt_vmpools) fact, which
       contains a list of vmpools."
options:
    pattern:
      description:
        - "Search term which is accepted by oVirt search backend."
        - "For example to search vmpool X: name=X"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all vm pools which names start with C(centos):
- ovirt_vmpools_facts:
    pattern: name=centos*
- debug:
    var: ovirt_vmpools
'''

RETURN = '''
ovirt_vm_pools:
    description: "List of dictionaries describing the vmpools. Vm pool attribues are mapped to dictionary keys,
                  all vmpools attributes can be found at following url: https://ovirt.example.com/ovirt-engine/api/model#types/vm_pool."
    returned: On success.
    type: list
'''


def main():
    argument_spec = ovirt_full_argument_spec(
        pattern=dict(default='', required=False),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        vmpools_service = connection.system_service().vm_pools_service()
        vmpools = vmpools_service.list(search=module.params['pattern'])
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_vm_pools=[
                    get_dict_of_struct(c) for c in vmpools
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=False)

if __name__ == '__main__':
    main()
