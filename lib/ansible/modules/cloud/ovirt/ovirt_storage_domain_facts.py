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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_storage_domain_facts
short_description: Retrieve facts about one or more oVirt/RHV storage domains
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt/RHV storage domains."
notes:
    - "This module creates a new top-level C(ovirt_storage_domains) fact, which
       contains a list of storage domains."
options:
    pattern:
      description:
        - "Search term which is accepted by oVirt/RHV search backend."
        - "For example to search storage domain X from datacenter Y use following pattern:
           name=X and datacenter=Y"
extends_documentation_fragment: ovirt_facts
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all storage domains which names start with C(data) and
# belong to data center C(west):
- ovirt_storage_domain_facts:
    pattern: name=data* and datacenter=west
- debug:
    var: ovirt_storage_domains
'''

RETURN = '''
ovirt_storage_domains:
    description: "List of dictionaries describing the storage domains. Storage_domain attributes are mapped to dictionary keys,
                  all storage domains attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/storage_domain."
    returned: On success.
    type: list
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
    argument_spec = ovirt_facts_full_argument_spec(
        pattern=dict(default='', required=False),
    )
    module = AnsibleModule(argument_spec)

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        storage_domains_service = connection.system_service().storage_domains_service()
        storage_domains = storage_domains_service.list(search=module.params['pattern'])
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_storage_domains=[
                    get_dict_of_struct(
                        struct=c,
                        connection=connection,
                        fetch_nested=module.params.get('fetch_nested'),
                        attributes=module.params.get('nested_attributes'),
                    ) for c in storage_domains
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
