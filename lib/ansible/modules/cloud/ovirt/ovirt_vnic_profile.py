#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_vnic_profile
short_description: Module to manage vNIC profile of network in oVirt/RHV
version_added: "2.8"
author:
- "Ondra Machacek (@machacekondra)"
- "Martin Necas (@mnecas)"
description:
    - "Module to manage vNIC profile of network in oVirt/RHV"
options:
    name:
        description:
            - "A human-readable name in plain text."
        required: true
    state:
        description:
            - "Should the vNIC be absent/present."
        choices: ['absent', 'present']
        default: present
    description:
        description:
            - "A human-readable description in plain text."
    data_center:
        description:
            - "Datacenter name where network reside."
        required: true
    network:
        description:
            - "Name of network to which is vNIC attached."
        required: true
    network_filter:
        description:
            - "The network filter enables to filter packets send to/from the VM's nic according to defined rules."
    custom_properties:
        description:
            - "Custom properties applied to the vNIC profile."
            - "Custom properties is a list of dictionary which can have following values:"
        suboptions:
            name:
                description:
                    - "Name of the custom property. For example: I(hugepages), I(vhost), I(sap_agent), etc."
            regexp:
                description:
                    - Regular expression to set for custom property.
            value:
                description:
                    - Value to set for custom property.
    qos:
        description:
            - "Quality of Service attributes regulate inbound and outbound network traffic of the NIC."
    port_mirroring:
        description:
            - "Enables port mirroring."
        type: bool
    pass_through:
        description:
            - "Enables passthrough to an SR-IOV-enabled host NIC."
        choices: ['disabled', 'enabled']
    migratable:
        description:
            - "Marks whether pass_through NIC is migratable or not."
        type: bool
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:
- name: Add vNIC
  ovirt_vnics_profile:
    name: myvnic
    network: mynetwork
    state: present
    data_center: datacenter

- name: Editing vNICs network_filter, custom_properties, qos
  ovirt_vnics_profile:
    name: myvnic
    network: mynetwork
    data_center: datacenter
    qos: myqos
    custom_properties:
      - name: SecurityGroups
        value: 9bd9bde9-39da-44a8-9541-aa39e1a81c9d
    network_filter: allow-dhcp

- name: Editing vNICs network_filter, custom_properties, qos
  ovirt_vnics_profile:
    name: myvnic
    network: mynetwork
    data_center: datacenter
    qos: myqos
    custom_properties:
      - name: SecurityGroups
        value: 9bd9bde9-39da-44a8-9541-aa39e1a81c9d
    network_filter: allow-dhcp

- name: Dont use migratable
  ovirt_vnics_profile:
    name: myvnic
    network: mynetwork
    data_center: datacenter
    migratable: False
    pass_through: enabled

- name: Remove vNIC
  ovirt_vnics_profile:
    name: myvnic
    network: mynetwork
    state: absent
    data_center: datacenter
'''

RETURN = '''
id:
    description: ID of the vNIC profile which is managed
    returned: On success if vNIC profile is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
vnic:
    description: "Dictionary of all the vNIC profile attributes. Network interface attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/nic."
    returned: On success if vNIC profile is found.
    type: dict
'''

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    get_link_name,
    ovirt_full_argument_spec,
    search_by_name,
    get_id_by_name
)


class EntityVnicPorfileModule(BaseModule):

    def __init__(self, *args, **kwargs):
        super(EntityVnicPorfileModule, self).__init__(*args, **kwargs)

    def __get_dcs_service(self):
        return self._connection.system_service().data_centers_service()

    def __get_dcs_id(self):
        return get_id_by_name(self.__get_dcs_service(), self.param('data_center'))

    def __get_network_id(self):
        networks_service = self.__get_dcs_service().service(self.__get_dcs_id()).networks_service()
        return get_id_by_name(networks_service, self.param('network'))

    def __get_qos_id(self):
        qoss_service = self.__get_dcs_service().service(self.__get_dcs_id()).qoss_service()
        return get_id_by_name(qoss_service, self.param('qos'))

    def __get_network_filter_id(self):
        nf_service = self._connection.system_service().network_filters_service()
        return get_id_by_name(nf_service, self.param('network_filter')) if self.param('network_filter') else None

    def build_entity(self):
        return otypes.VnicProfile(
            name=self.param('name'),
            network=otypes.Network(id=self.__get_network_id()),
            description=self.param('description')
            if self.param('description') else None,
            port_mirroring=self.param('port_mirroring'),
            pass_through=otypes.VnicPassThrough(mode=otypes.VnicPassThroughMode(self.param('pass_through')))
            if self.param('pass_through') else None,
            migratable=self.param('migratable'),
            custom_properties=[
                otypes.CustomProperty(
                    name=cp.get('name'),
                    regexp=cp.get('regexp'),
                    value=str(cp.get('value')),
                ) for cp in self.param('custom_properties') if cp
            ] if self.param('custom_properties') is not None else None,
            qos=otypes.Qos(id=self.__get_qos_id())
            if self.param('qos') else None,
            network_filter=otypes.NetworkFilter(id=self.__get_network_filter_id())
            if self.param('network_filter') is not None else None
        )

    def update_check(self, entity):
        def check_custom_properties():
            if self.param('custom_properties'):
                current = []
                if entity.custom_properties:
                    current = [(cp.name, cp.regexp, str(cp.value)) for cp in entity.custom_properties]
                passed = [(cp.get('name'), cp.get('regexp'), str(cp.get('value'))) for cp in self.param('custom_properties') if cp]
                return sorted(current) == sorted(passed)
            return True

        return (
            check_custom_properties() and
            equal(self.param('migratable'), getattr(entity, 'migratable', None)) and
            equal(self.param('pass_through'), entity.pass_through.mode.name) and
            equal(self.param('description'), entity.description) and
            equal(self.param('network_filter'), getattr(entity.network_filter, 'name', None)) and
            equal(self.param('qos'), entity.qos.name) and
            equal(self.param('port_mirroring'), getattr(entity, 'port_mirroring', None))
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        network=dict(type='str', required=True),
        data_center=dict(type='str', required=True),
        description=dict(type='str'),
        name=dict(type='str', required=True),
        network_filter=dict(type='str'),
        custom_properties=dict(type='list'),
        qos=dict(type='str'),
        pass_through=dict(type='str', choices=['disabled', 'enabled']),
        port_mirroring=dict(type='bool'),
        migratable=dict(type='bool'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,

    )
    check_sdk(module)
    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)

        vnic_services = connection.system_service().vnic_profiles_service()

        entitynics_module = EntityVnicPorfileModule(
            connection=connection,
            module=module,
            service=vnic_services,
        )
        state = module.params['state']
        if state == 'present':
            ret = entitynics_module.create()
        elif state == 'absent':
            ret = entitynics_module.remove()

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
