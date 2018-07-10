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
module: ovirt_storage_templates_facts
short_description: Retrieve facts about one or more oVirt/RHV templates relate to a storage domain.
author: "Maor Lipchuk"
version_added: "2.4"
description:
    - "Retrieve facts about one or more oVirt/RHV templates relate to a storage domain."
notes:
    - "This module creates a new top-level C(ovirt_storage_templates) fact, which
       contains a list of templates."
options:
    unregistered:
        description:
            - "Flag which indicates whether to get unregistered templates which contain one or more
               disks which reside on a storage domain or diskless templates."

extends_documentation_fragment: ovirt_facts
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all Templates which relate to a storage domain and
# are unregistered:
- ovirt_storage_templates_facts:
    unregistered=True
- debug:
    var: ovirt_storage_templates
'''

RETURN = '''
ovirt_storage_templates:
    description: "List of dictionaries describing the Templates. Template attribues are mapped to dictionary keys,
                  all Templates attributes can be found at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/template."
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
    get_id_by_name
)


def main():
    argument_spec = ovirt_facts_full_argument_spec(
        all_content=dict(default=False, type='bool'),
        case_sensitive=dict(default=True, type='bool'),
        storage_domain=dict(default=None),
        max=dict(default=None, type='int'),
        unregistered=dict(default=False, type='bool'),
    )
    module = AnsibleModule(argument_spec)
    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        storage_domains_service = connection.system_service().storage_domains_service()
        sd_id = get_id_by_name(storage_domains_service, module.params['storage_domain'])
        storage_domain_service = storage_domains_service.storage_domain_service(sd_id)
        templates_service = storage_domain_service.templates_service()

        # Find the the unregistered Template we want to register:
        if module.params.get('unregistered'):
            templates = templates_service.list(unregistered=True)
        else:
            templates = templates_service.list()
        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_storage_templates=[
                    get_dict_of_struct(
                        struct=c,
                        connection=connection,
                        fetch_nested=module.params.get('fetch_nested'),
                        attributes=module.params.get('nested_attributes'),
                    ) for c in templates
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
