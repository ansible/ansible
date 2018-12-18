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
module: ovirt_external_provider
short_description: Module to manage external providers in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage external providers in oVirt/RHV"
options:
    name:
        description:
            - "Name of the external provider to manage."
    state:
        description:
            - "Should the external be present or absent"
            - "When you are using absent for I(os_volume), you need to make
               sure that SD is not attached to the data center!"
        choices: ['present', 'absent']
        default: present
    description:
        description:
            - "Description of the external provider."
    type:
        description:
            - "Type of the external provider."
        choices: ['os_image', 'network', 'os_volume', 'foreman']
    url:
        description:
            - "URL where external provider is hosted."
            - "Applicable for those types: I(os_image), I(os_volume), I(network) and I(foreman)."
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
            - "Applicable for those types: I(os_image), I(os_volume) and I(network)."
        aliases: ['tenant']
    authentication_url:
        description:
            - "Keystone authentication URL of the openstack provider."
            - "Applicable for those types: I(os_image), I(os_volume) and I(network)."
        aliases: ['auth_url']
    data_center:
        description:
            - "Name of the data center where provider should be attached."
            - "Applicable for those type: I(os_volume)."
    read_only:
        description:
            - "Specify if the network should be read only."
            - "Applicable if C(type) is I(network)."
        type: bool
    network_type:
        description:
            - "Type of the external network provider either external (for example OVN) or neutron."
            - "Applicable if C(type) is I(network)."
        choices: ['external', 'neutron']
        default: ['external']
    authentication_keys:
        description:
            - "List of authentication keys. Each key is represented by dict
               like {'uuid': 'our-uuid', 'value': 'YourSecretValue=='}"
            - "When you will not pass these keys and there are already some
               of them defined in the system they will be removed."
            - "Applicable for I(os_volume)."
        default: []
        version_added: "2.6"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Add image external provider:
- ovirt_external_provider:
    name: image_provider
    type: os_image
    url: http://1.2.3.4:9292
    username: admin
    password: 123456
    tenant: admin
    auth_url: http://1.2.3.4:35357/v2.0

# Add volume external provider:
- ovirt_external_provider:
    name: image_provider
    type: os_volume
    url: http://1.2.3.4:9292
    username: admin
    password: 123456
    tenant: admin
    auth_url: http://1.2.3.4:5000/v2.0
    authentication_keys:
      -
        uuid: "1234567-a1234-12a3-a234-123abc45678"
        value: "ABCD00000000111111222333445w=="

# Add foreman provider:
- ovirt_external_provider:
    name: foreman_provider
    type: foreman
    url: https://foreman.example.com
    username: admin
    password: 123456

# Add external network provider for OVN:
- ovirt_external_provider:
    name: ovn_provider
    type: network
    network_type: external
    url: http://1.2.3.4:9696

# Remove image external provider:
- ovirt_external_provider:
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
    description: "Dictionary of all the external_host_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/external_host_provider."
    returned: "On success and if parameter 'type: foreman' is used."
    type: dict
openstack_image_provider:
    description: "Dictionary of all the openstack_image_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/openstack_image_provider."
    returned: "On success and if parameter 'type: os_image' is used."
    type: dict
openstack_volume_provider:
    description: "Dictionary of all the openstack_volume_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/openstack_volume_provider."
    returned: "On success and if parameter 'type: os_volume' is used."
    type: dict
openstack_network_provider:
    description: "Dictionary of all the openstack_network_provider attributes. External provider attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/openstack_network_provider."
    returned: "On success and if parameter 'type: network' is used."
    type: dict
'''

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


OS_VOLUME = 'os_volume'
OS_IMAGE = 'os_image'
NETWORK = 'network'
FOREMAN = 'foreman'


class ExternalProviderModule(BaseModule):

    non_provider_params = ['type', 'authentication_keys', 'data_center']

    def provider_type(self, provider_type):
        self._provider_type = provider_type

    def provider_module_params(self):
        provider_params = [
            (key, value) for key, value in self._module.params.items() if key
            not in self.non_provider_params
        ]
        provider_params.append(('data_center', self.get_data_center()))
        return provider_params

    def get_data_center(self):
        dc_name = self._module.params.get("data_center", None)
        if dc_name:
            system_service = self._connection.system_service()
            data_centers_service = system_service.data_centers_service()
            return data_centers_service.list(
                search='name=%s' % dc_name,
            )[0]
        return dc_name

    def build_entity(self):
        provider_type = self._provider_type(
            requires_authentication=self._module.params.get('username') is not None,
        )
        if self._module.params.pop('type') == NETWORK:
            setattr(
                provider_type,
                'type',
                otypes.OpenStackNetworkProviderType(self._module.params.pop('network_type'))
            )

        for key, value in self.provider_module_params():
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

    def update_volume_provider_auth_keys(
        self, provider, providers_service, keys
    ):
        """
        Update auth keys for volume provider, if not exist add them or remove
        if they are not specified and there are already defined in the external
        volume provider.

        Args:
            provider (dict): Volume provider details.
            providers_service (openstack_volume_providers_service): Provider
                service.
            keys (list): Keys to be updated/added to volume provider, each key
                is represented as dict with keys: uuid, value.
        """

        provider_service = providers_service.provider_service(provider['id'])
        auth_keys_service = provider_service.authentication_keys_service()
        provider_keys = auth_keys_service.list()
        # removing keys which are not defined
        for key in [
            k.id for k in provider_keys if k.uuid not in [
                defined_key['uuid'] for defined_key in keys
            ]
        ]:
            self.changed = True
            if not self._module.check_mode:
                auth_keys_service.key_service(key).remove()
        if not (provider_keys or keys):
            # Nothing need to do when both are empty.
            return
        for key in keys:
            key_id_for_update = None
            for existing_key in provider_keys:
                if key['uuid'] == existing_key.uuid:
                    key_id_for_update = existing_key.id

            auth_key_usage_type = (
                otypes.OpenstackVolumeAuthenticationKeyUsageType("ceph")
            )
            auth_key = otypes.OpenstackVolumeAuthenticationKey(
                usage_type=auth_key_usage_type,
                uuid=key['uuid'],
                value=key['value'],
            )

            if not key_id_for_update:
                self.changed = True
                if not self._module.check_mode:
                    auth_keys_service.add(auth_key)
            else:
                # We cannot really distinguish here if it was really updated cause
                # we cannot take key value to check if it was changed or not. So
                # for sure we update here always.
                self.changed = True
                if not self._module.check_mode:
                    auth_key_service = (
                        auth_keys_service.key_service(key_id_for_update)
                    )
                    auth_key_service.update(auth_key)


def _external_provider_service(provider_type, system_service):
    if provider_type == OS_IMAGE:
        return otypes.OpenStackImageProvider, system_service.openstack_image_providers_service()
    elif provider_type == NETWORK:
        return otypes.OpenStackNetworkProvider, system_service.openstack_network_providers_service()
    elif provider_type == OS_VOLUME:
        return otypes.OpenStackVolumeProvider, system_service.openstack_volume_providers_service()
    elif provider_type == FOREMAN:
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
                OS_IMAGE, NETWORK, OS_VOLUME, FOREMAN,
            ],
            aliases=['provider'],
        ),
        url=dict(default=None),
        username=dict(default=None),
        password=dict(default=None, no_log=True),
        tenant_name=dict(default=None, aliases=['tenant']),
        authentication_url=dict(default=None, aliases=['auth_url']),
        data_center=dict(default=None),
        read_only=dict(default=None, type='bool'),
        network_type=dict(
            default='external',
            choices=['external', 'neutron'],
        ),
        authentication_keys=dict(
            default=[], aliases=['auth_keys'], type='list', no_log=True,
        ),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)
    check_params(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        provider_type_param = module.params.get('type')
        provider_type, external_providers_service = _external_provider_service(
            provider_type=provider_type_param,
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
            openstack_volume_provider_id = ret.get('id')
            if (
                provider_type_param == OS_VOLUME and
                openstack_volume_provider_id
            ):
                external_providers_module.update_volume_provider_auth_keys(
                    ret, external_providers_service,
                    module.params.get('authentication_keys'),
                )

        module.exit_json(**ret)

    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
