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
module: ovirt_external_provider_facts
short_description: Retrieve facts about one or more oVirt/RHV external providers
author: "Ondra Machacek (@machacekondra)"
version_added: "2.3"
description:
    - "Retrieve facts about one or more oVirt/RHV external providers."
notes:
    - "This module creates a new top-level C(ovirt_external_providers) fact, which
       contains a list of external_providers."
options:
    type:
        description:
            - "Type of the external provider."
        choices: ['os_image', 'os_network', 'os_volume', 'foreman']
        required: true
    name:
        description:
            - "Name of the external provider, can be used as glob expression."
extends_documentation_fragment: ovirt_facts
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Gather facts about all image external providers named C<glance>:
- ovirt_external_provider_facts:
    type: os_image
    name: glance
- debug:
    var: ovirt_external_providers
'''

RETURN = '''
external_host_providers:
    description: "List of dictionaries of all the external_host_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/external_host_provider."
    returned: "On success and if parameter 'type: foreman' is used."
    type: list
openstack_image_providers:
    description: "List of dictionaries of all the openstack_image_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/openstack_image_provider."
    returned: "On success and if parameter 'type: os_image' is used."
    type: list
openstack_volume_providers:
    description: "List of dictionaries of all the openstack_volume_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/openstack_volume_provider."
    returned: "On success and if parameter 'type: os_volume' is used."
    type: list
openstack_network_providers:
    description: "List of dictionaries of all the openstack_network_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/openstack_network_provider."
    returned: "On success and if parameter 'type: os_network' is used."
    type: list
'''

import fnmatch
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    check_sdk,
    create_connection,
    get_dict_of_struct,
    ovirt_facts_full_argument_spec,
)


def _external_provider_service(provider_type, system_service):
    if provider_type == 'os_image':
        return system_service.openstack_image_providers_service()
    elif provider_type == 'os_network':
        return system_service.openstack_network_providers_service()
    elif provider_type == 'os_volume':
        return system_service.openstack_volume_providers_service()
    elif provider_type == 'foreman':
        return system_service.external_host_providers_service()


def main():
    argument_spec = ovirt_facts_full_argument_spec(
        name=dict(default=None, required=False),
        type=dict(
            default=None,
            required=True,
            choices=[
                'os_image', 'os_network', 'os_volume', 'foreman',
            ],
            aliases=['provider'],
        ),
    )
    module = AnsibleModule(argument_spec)

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        external_providers_service = _external_provider_service(
            provider_type=module.params.pop('type'),
            system_service=connection.system_service(),
        )
        if module.params['name']:
            external_providers = [
                e for e in external_providers_service.list()
                if fnmatch.fnmatch(e.name, module.params['name'])
            ]
        else:
            external_providers = external_providers_service.list()

        module.exit_json(
            changed=False,
            ansible_facts=dict(
                ovirt_external_providers=[
                    get_dict_of_struct(
                        struct=c,
                        connection=connection,
                        fetch_nested=module.params.get('fetch_nested'),
                        attributes=module.params.get('nested_attributes'),
                    ) for c in external_providers
                ],
            ),
        )
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == '__main__':
    main()
