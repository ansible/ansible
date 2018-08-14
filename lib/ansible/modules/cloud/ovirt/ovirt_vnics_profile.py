#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ovirt_vnics
short_description: Module to manage network interfaces of Virtual Machines in oVirt/RHV
version_added: "2.7"
author:
- Martin Necas (@mnecas)
description:
    - Module to manage network interfaces of Virtual Machines in oVirt/RHV.
options:

extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

'''

RETURN = '''
id:
    description: ID of the network interface which is managed
    returned: On success if network interface is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
vnic:
    description: "Dictionary of all the network interface attributes. Network interface attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/nic."
    returned: On success if network interface is found.
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
        self.vnic_id = None

    def build_entity(self):
        dcs_service = self._connection.system_service().data_centers_service()
        dc = dcs_service.list(search='name=%s' % self._module.params.get('data_center'))[0]
        networks_service = dcs_service.service(dc.id).networks_service()
        network = next(
            (n for n in networks_service.list()
                if n.name == self._module.params['network']),
            None
        )
        if network is None:
            raise Exception(
                "Network '%s' was not found in datacenter '%s'." % (
                    self._module.params['network'],
                    dc.name
                )
            )

        return otypes.VnicProfile(
            name=self._module.params.get('name'),
            network=network,
            description=self._module.params.get('description')
            if self._module.params.get('description') else None,
            port_mirroring=self._module.params.get('port_mirroring')
            if self._module.params.get('port_mirroring') else None,
            pass_through=otypes.VnicPassThrough(mode=otypes.VnicPassThroughMode(self._module.params.get('pass_through')))
            if self._module.params.get('pass_through') else None,
            migratable=self._module.params.get('migratable')
            if self._module.params.get('migratable') else None
        )

    def update_check(self, entity):
        return (
            equal(self._module.params.get('migratable'), entity.migratable) and
            equal(self._module.params.get('pass_through'), entity.pass_through) and
            equal(self._module.params.get('description'), entity.description) and
            # equal(self._module.params.get('network_filter'), entity.network_filter) and
            equal(self._module.params.get('port_mirroring'), entity.port_mirroring)
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(type='str', default='present', choices=['absent', 'present']),
        network=dict(type='str'),
        data_center=dict(type='str'),
        description=dict(type='str'),
        name=dict(type='str', required=True),
        # network_filter=dict(type='str'),
        # custom_properties=dict(type='dict'),
        # qos=dict(type='str'),
        pass_through=dict(type='str'),
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
        #service = vnic_services.service(get_id_by_name(vnic_services,module.params['name']))

        entitynics_module = EntityVnicPorfileModule(
            connection=connection,
            module=module,
            service=vnic_services,
        )
        """
            custom_properties=[
                otypes.CustomProperty(
                    name=cp.get('name'),
                    regexp=cp.get('regexp'),
                    value=str(cp.get('value')),
                ) for cp in self.param('custom_properties') if cp
            ] if self.param('custom_properties') is not None else None,"""
        # custom_properties=[otypes.CustomProperty(name=prop['name'],value=prop['value'],regexp=prop['regexp']) for prop in module.params['custom_properties']]
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
