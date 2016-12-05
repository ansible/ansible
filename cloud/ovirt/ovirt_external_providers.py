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

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_params,
    check_sdk,
    create_connection,
    equal,
    ovirt_full_argument_spec,
)


DOCUMENTATION = '''
---
module: ovirt_external_providers
short_description: Module to manage external providers in oVirt
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage external providers in oVirt"
options:
    name:
        description:
            - "Name of the the external provider to manage."
    state:
        description:
            - "Should the external be present or absent"
        choices: ['present', 'absent']
        default: present
    description:
        description:
            - "Description of the external provider."
    type:
        description:
            - "Type of the external provider."
        choices: ['os_image', 'os_network', 'os_volume', 'foreman']
    url:
        description:
            - "URL where external provider is hosted."
            - "Applicable for those types: I(os_image), I(os_volume), I(os_network) and I(foreman)."
    username:
        description:
            - "Username to be used for login to external provider."
            - "Applicable for all types."
    password:
        description:
            - "Password of the user specified in C(username) parameter."
            - "Applicable for all types."
    tenant_name:
        description:
            - "Name of the tenant."
            - "Applicable for those types: I(os_image), I(os_volume) and I(os_network)."
        aliases: ['tenant']
    authentication_url:
        description:
            - "Keystone authentication URL of the openstack provider."
            - "Applicable for those types: I(os_image), I(os_volume) and I(os_network)."
        aliases: ['auth_url']
    data_center:
        description:
            - "Name of the data center where provider should be attached."
            - "Applicable for those type: I(os_volume)."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add image external provider:
- ovirt_external_providers:
    name: image_provider
    type: os_image
    url: http://10.34.63.71:9292
    username: admin
    password: 123456
    tenant: admin
    auth_url: http://10.34.63.71:35357/v2.0/

# Add foreman provider:
- ovirt_external_providers:
    name: foreman_provider
    type: foreman
    url: https://foreman.example.com
    username: admin
    password: 123456

# Remove image external provider:
- ovirt_external_providers:
    state: absent
    name: image_provider
    type: os_image
'''

RETURN = '''
id:
    description: ID of the external provider which is managed
    returned: On success if external provider is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
external_host_provider:
    description: "Dictionary of all the external_host_provider attributes. External provider attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/external_host_provider."
    returned: "On success and if parameter 'type: foreman' is used."
    type: dictionary
openstack_image_provider:
    description: "Dictionary of all the openstack_image_provider attributes. External provider attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/openstack_image_provider."
    returned: "On success and if parameter 'type: os_image' is used."
    type: dictionary
openstack_volume_provider:
    description: "Dictionary of all the openstack_volume_provider attributes. External provider attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/openstack_volume_provider."
    returned: "On success and if parameter 'type: os_volume' is used."
    type: dictionary
openstack_network_provider:
    description: "Dictionary of all the openstack_network_provider attributes. External provider attributes can be found on your oVirt instance
                  at following url: https://ovirt.example.com/ovirt-engine/api/model#types/openstack_network_provider."
    returned: "On success and if parameter 'type: os_network' is used."
    type: dictionary
'''


class ExternalProviderModule(BaseModule):

    def provider_type(self, provider_type):
        self._provider_type = provider_type

    def build_entity(self):
        provider_type = self._provider_type(
            requires_authentication='username' in self._module.params,
        )
        for key, value in self._module.params.items():
            if hasattr(provider_type, key):
                setattr(provider_type, key, value)

        return provider_type

    def update_check(self, entity):
        return (
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('url'), entity.url) and
            equal(self._module.params.get('authentication_url'), entity.authentication_url) and
            equal(self._module.params.get('tenant_name'), getattr(entity, 'tenant_name', None)) and
            equal(self._module.params.get('username'), entity.username)
        )


def _external_provider_service(provider_type, system_service):
    if provider_type == 'os_image':
        return otypes.OpenStackImageProvider, system_service.openstack_image_providers_service()
    elif provider_type == 'os_network':
        return otypes.OpenStackNetworkProvider, system_service.openstack_network_providers_service()
    elif provider_type == 'os_volume':
        return otypes.OpenStackVolumeProvider, system_service.openstack_volume_providers_service()
    elif provider_type == 'foreman':
        return otypes.ExternalHostProvider, system_service.external_host_providers_service()


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(default=None),
        description=dict(default=None),
        type=dict(
            default=None,
            required=True,
            choices=[
                'os_image', 'os_network', 'os_volume',  'foreman',
            ],
            aliases=['provider'],
        ),
        url=dict(default=None),
        username=dict(default=None),
        password=dict(default=None, no_log=True),
        tenant_name=dict(default=None, aliases=['tenant']),
        authentication_url=dict(default=None, aliases=['auth_url']),
        data_center=dict(default=None, aliases=['data_center']),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    check_sdk(module)
    check_params(module)

    try:
        connection = create_connection(module.params.pop('auth'))
        provider_type, external_providers_service = _external_provider_service(
            provider_type=module.params.pop('type'),
            system_service=connection.system_service(),
        )
        external_providers_module = ExternalProviderModule(
            connection=connection,
            module=module,
            service=external_providers_service,
        )
        external_providers_module.provider_type(provider_type)

        state = module.params.pop('state')
        if state == 'absent':
            ret = external_providers_module.remove()
        elif state == 'present':
            ret = external_providers_module.create()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=False)


if __name__ == "__main__":
    main()
