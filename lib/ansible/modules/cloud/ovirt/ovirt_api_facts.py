#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat, Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_api_facts
short_description: Retrieve facts about the oVirt/RHV API
author: "Ondra Machacek (@machacekondra)"
version_added: "2.5"
description:
    - "Retrieve facts about the oVirt/RHV API."
notes:
    - "This module creates a new top-level C(ovirt_api) fact,
       which contains a information about oVirt/RHV API."
extends_documentation_fragment: ovirt_facts
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts oVirt API:
- ovirt_api_facts:
- debug:
    var: ovirt_api
'''

RETURN = '''
ovirt_api:
    description: "Dictionary describing the oVirt API information.
                  Api attributes are mapped to dictionary keys,
                  all API attributes can be found at following
                  url: https://ovirt.example.com/ovirt-engine/api/model#types/api."
    returned: On success.
    type: dictionary
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_facts_full_argument_spec,
)


def main():
    argument_spec = ovirt_facts_full_argument_spec()
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        api = connection.system_service().get()
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_api=get_dict_of_struct(
                    struct=api,
                    connection=connection,
                    fetch_nested=module.params.get('fetch_nested'),
                    attributes=module.params.get('nested_attributes'),
                )
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
