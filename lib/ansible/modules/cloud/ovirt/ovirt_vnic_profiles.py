#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Red Hat, Inc.
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
module: ovirt_vnic_profiles
short_description: Module to manage vNIC profiles in oVirt/RHV.
version_added: "2.6"
author:
- Leon Goldberg (@leongold)
description:
    - Module to manage vNIC profiles in oVirt/RHV.
options:
    name:
        description:
            - "Name of the vNIC profile."
        required: true
    data_center:
        description:
            - "Name of the underlying network's data center."
        required: true
    description:
        description:
            - "Description of the vNIC profile."
    comment:
        description:
            - "Comment for the vNIC profile."
    network:
        description:
            - "The vNIC profile's underlying network name."
        required: true
    pass_through:
        description:
            - "Determines whether device passthrough should be enabeld for the vNIC's."
        choices: [ enabled, disabled ]
    network_filter:
        description:
            - "Name of a network filter the vNIC's should use."
    migratable:
        description:
            - "Determines whether the vNIC's should be migratable."
    port_mirroring:
        description:
            - "Determines whether port mirroring should be enabled for the vNIC's."
    qos:
        description:
            - "Name of a network QoS to apply to the vNIC's.""
    custom_properties:
        description:
            - "Properties sent to VDSM to configure various hooks."
            - "Custom properties is a list of dictionary which can have following values:"
            - "C(name) - Name of the custom property."
            - "C(regexp) - Regular expression to set for custom property."
            - "C(value) - Value to set for custom property."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

- name: Create passthrough vNIC profile
  ovirt_vnic_profiles:
    state: present
    name: vnic-profile-0
    data_center: Default
    network: ovirtmgmt
    pass_through: enabled

- name: Remove vNIC profile
  ovirt_vnic_profiles:
    state: absent
    name: vnic-profile-0
    data_center: Default
    network: ovirtmgmt
'''

RETURN = '''
id:
    description: ID of the vNIC profile.
    returned: On success if the vNIC profile is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
nic:
    description: "Dictionary of all the vNIC profile attributes. vNIC profile attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#services/vnic_profile."
    returned: On success if the vNIC profile is found.
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
    check_sdk,
    check_params,
    create_connection,
    equal,
    ovirt_full_argument_spec,
    search_by_name,
)


class VnicprofilesModule(BaseModule):

    def build_entity(self):
        return otypes.VnicProfile(
            name=self.param('name'),
            comment=self.param('comment'),
            description=self.param('description'),
            migratable=self.param('migratable'),
            network=self._get_network(),
            pass_through=otypes.VnicPassThrough(
                otypes.VnicPassThroughMode(self.param('pass_through'))
            ),
            port_mirroring=self.param('port_mirroring'),
            network_filter=self._get_network_filter(),
            custom_properties=self._get_custom_properties(),
            qos=self._get_qos()
        )

    def _get_dc(self):
        dc_name = self.param('data_center')
        dc = search_by_name(
            self._connection.system_service().data_centers_service(), dc_name
        )
        if not dc:
            raise Exception("Data center '%s' was not found." % (dc_name,))
        return dc

    def _get_network(self):
        dc = self._get_dc()

        networks_service = self._connection.system_service().data_centers_service().service(dc.id).networks_service()
        network = search_by_name(networks_service, self.param('network'))
        if not network:
            raise Exception("Network '%s' was not found." % (network,))
        return network

    def _get_custom_properties(self):
        custom_properties = self.param('custom_properties')
        if not custom_properties:
            return None

        return [
            otypes.CustomProperty(
                name=cp.get('name'),
                regexp=cp.get('regexp'),
                value=str(cp.get('value'))
            ) for cp in custom_properties
        ]

    def _get_network_filter(self):
        nf_name = self.param('network_filter')
        if not nf_name:
            return None

        network_filters_service = self._connection.system_service().network_filters_service()
        network_filter = search_by_name(network_filters_service, nf_name)
        if not network_filter:
            raise Exception("Network filter '%s' was not found." % (network_filter,))
        return network_filter

    def _get_qos(self):
        qos_name = self.param('qos')
        if not qos_name:
            return None

        dc = self._get_dc()
        qos = search_by_name(
            self._connection.system_service().data_centers_service().service(dc.id).qoss_service(),
            qos_name
        )
        if not qos:
            raise Exception("QoS '%s' was not found." % (qos_name,))
        return qos

    def update_check(self, entity):
        def check_custom_properties():
            if self.param('custom_properties'):
                current = []
                if entity.custom_properties:
                    current = [(cp.name, cp.regexp, str(cp.value)) for cp in entity.custom_properties]
                passed = [(cp.get('name'), cp.get('regexp'), str(cp.get('value'))) for cp in self.param('custom_properties')]
                return sorted(current) == sorted(passed)
            return True

        def check_qos():
            qos = self._get_qos()
            if qos:
                if entity.qos:
                    return qos.id == entity.qos.id
            return True

        def check_network_filter():
            nf = self._get_network_filter()
            if nf:
                if entity.network_filter:
                    return nf.id == entity.network_filter.id
            return True

        return (
            equal(self.param('name'), entity.name) and
            equal(self.param('comment'), entity.comment) and
            equal(self.param('description'), entity.description) and
            equal(self.param('migratable'), entity.migratable) and
            equal(self._get_network().id, entity.network.id) and
            equal(self.param('pass_through'), str(entity.pass_through.mode)) and
            equal(self.param('port_mirroring'), entity.port_mirroring) and
            check_custom_properties() and
            check_qos() and
            check_network_filter()
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        name=dict(required=True, type='str'),
        data_center=dict(required=True, type='str'),
        comment=dict(default=None, type='str'),
        description=dict(default=None, type='str'),
        migratable=dict(default=None, type='bool'),
        network=dict(required=True, type='str'),
        network_filter=dict(default=None, type='str'),
        pass_through=dict(type='str', default='disabled', choices=['disabled', 'enabled']),
        port_mirroring=dict(default=False, type='bool'),
        qos=dict(default=None, type='str'),
        custom_properties=dict(default=None, type='list')
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

        vnic_profiles_service = connection.system_service().vnic_profiles_service()
        vnic_profiles_module = VnicprofilesModule(
            connection=connection,
            module=module,
            service=vnic_profiles_service,
        )

        state = module.params['state']
        if state == 'present':
            ret = vnic_profiles_module.create()
        elif state == 'absent':
            ret = vnic_profiles_module.remove(force=module.params['force'])

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
