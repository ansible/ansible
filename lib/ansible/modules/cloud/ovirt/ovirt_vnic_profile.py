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
            - "When enabled C(qos) and  C(network_filter) are automatically set to None and C(port_mirroring) to False."
            - "When enabled and C(migratable) not specified then C(migratable) is enabled."
            - "Port mirroring, QoS and network filters are not supported on passthrough profiles."
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
  ovirt_vnic_profile:
    name: myvnic
    network: mynetwork
    state: present
    data_center: datacenter

- name: Editing vNICs network_filter, custom_properties, qos
  ovirt_vnic_profile:
    name: myvnic
    network: mynetwork
    data_center: datacenter
    qos: myqos
    custom_properties:
      - name: SecurityGroups
        value: 9bd9bde9-39da-44a8-9541-aa39e1a81c9d
    network_filter: allow-dhcp

- name: Remove vNICs network_filter, custom_properties, qos
  ovirt_vnic_profile:
    name: myvnic
    network: mynetwork
    data_center: datacenter
    qos: ""
    custom_properties: ""
    network_filter: ""

- name: Dont use migratable
  ovirt_vnic_profile:
    name: myvnic
    network: mynetwork
    data_center: datacenter
    migratable: False
    pass_through: enabled

- name: Remove vNIC
  ovirt_vnic_profile:
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

    def _get_dcs_service(self):
        return self._connection.system_service().data_centers_service()

    def _get_dcs_id(self):
        return get_id_by_name(self._get_dcs_service(), self.param('data_center'))

    def _get_network_id(self):
        networks_service = self._get_dcs_service().service(self._get_dcs_id()).networks_service()
        return get_id_by_name(networks_service, self.param('network'))

    def _get_qos_id(self):
        if self.param('qos'):
            qoss_service = self._get_dcs_service().service(self._get_dcs_id()).qoss_service()
            return get_id_by_name(qoss_service, self.param('qos')) if self.param('qos') else None
        return None

    def _get_network_filter_id(self):
        nf_service = self._connection.system_service().network_filters_service()
        return get_id_by_name(nf_service, self.param('network_filter')) if self.param('network_filter') else None

    def _get_network_filter(self):
        network_filter = None
        # The order of these condition is necessary.
        # When would network_filter and pass_through specified it would try to create and network_filter and fail on engine.
        if self.param('network_filter') == '' or self.param('pass_through') == 'enabled':
            network_filter = otypes.NetworkFilter()
        elif self.param('network_filter'):
            network_filter = otypes.NetworkFilter(id=self._get_network_filter_id())
        return network_filter

    def _get_qos(self):
        qos = None
        # The order of these condition is necessary. When would qos and pass_through specified it would try to create and qos and fail on engine.
        if self.param('qos') == '' or self.param('pass_through') == 'enabled':
            qos = otypes.Qos()
        elif self.param('qos'):
            qos = otypes.Qos(id=self._get_qos_id())
        return qos

    def _get_port_mirroring(self):
        if self.param('pass_through') == 'enabled':
            return False
        return self.param('port_mirroring')

    def _get_migratable(self):
        if self.param('migratable') is not None:
            return self.param('migratable')
        if self.param('pass_through') == 'enabled':
            return True

    def build_entity(self):
        return otypes.VnicProfile(
            name=self.param('name'),
            network=otypes.Network(id=self._get_network_id()),
            description=self.param('description') if self.param('description') is not None else None,
            pass_through=otypes.VnicPassThrough(mode=otypes.VnicPassThroughMode(self.param('pass_through'))) if self.param('pass_through') else None,
            custom_properties=[
                otypes.CustomProperty(
                    name=cp.get('name'),
                    regexp=cp.get('regexp'),
                    value=str(cp.get('value')),
                ) for cp in self.param('custom_properties') if cp
            ] if self.param('custom_properties') else None,
            migratable=self._get_migratable(),
            qos=self._get_qos(),
            port_mirroring=self._get_port_mirroring(),
            network_filter=self._get_network_filter()
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

        pass_through = getattr(entity.pass_through.mode, 'name', None)
        return (
            check_custom_properties() and
            # The reason why we can't use equal method, is we get None from _get_network_filter_id or _get_qos_id method, when passing empty string.
            # And when first param of equal method is None it returns true.
            self._get_network_filter_id() == getattr(entity.network_filter, 'id', None) and
            self._get_qos_id() == getattr(entity.qos, 'id', None) and
            equal(self.param('migratable'), getattr(entity, 'migratable', None)) and
            equal(self.param('pass_through'), pass_through.lower() if pass_through else None) and
            equal(self.param('description'), entity.description) and
            equal(self.param('port_mirroring'), getattr(entity, 'port_mirroring', None))
        )


def get_entity(vnic_services, entitynics_module):
    vnic_profiles = vnic_services.list()
    network_id = entitynics_module._get_network_id()
    for vnic in vnic_profiles:
        # When vNIC already exist update it, when not create it
        if vnic.name == entitynics_module.param('name') and network_id == vnic.network.id:
            return vnic


def check_params(module):
    if (module.params.get('port_mirroring') or module.params.get('network_filter') or module.params.get('qos'))\
            and module.params.get('pass_through') == 'enabled':
        module.fail_json(msg="Cannot edit VM network interface profile. 'Port Mirroring,'Qos' and 'Network Filter' are not supported on passthrough profiles.")


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
    check_params(module)
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
        entity = get_entity(vnic_services, entitynics_module)
        if state == 'present':
            ret = entitynics_module.create(entity=entity, force_create=entity is None)
        elif state == 'absent':
            if entity is not None:
                ret = entitynics_module.remove(entity=entity)
            else:
                raise Exception("Vnic profile '%s' in network '%s' was not found." % (module.params['name'], module.params['network']))
        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
