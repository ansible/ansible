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
module: ovirt_networks
short_description: Module to manage logical networks in oVirt/RHV
version_added: "2.3"
author: "Ondra Machacek (@machacekondra)"
description:
    - "Module to manage logical networks in oVirt/RHV"
options:
    name:
        description:
            - "Name of the network to manage."
        required: true
    state:
        description:
            - "Should the network be present or absent"
        choices: ['present', 'absent']
        default: present
    data_center:
        description:
            - "Datacenter name where network reside."
    description:
        description:
            - "Description of the network."
    comment:
        description:
            - "Comment of the network."
    vlan_tag:
        description:
            - "Specify VLAN tag."
    vm_network:
        description:
            - "If I(True) network will be marked as network for VM."
            - "VM network carries traffic relevant to the virtual machine."
    mtu:
        description:
            - "Maximum transmission unit (MTU) of the network."
    clusters:
        description:
            - "List of dictionaries describing how the network is managed in specific cluster."
            - "C(name) - Cluster name."
            - "C(assigned) - I(true) if the network should be assigned to cluster. Default is I(true)."
            - "C(required) - I(true) if the network must remain operational for all hosts associated with this network."
            - "C(display) - I(true) if the network should marked as display network."
            - "C(migration) - I(true) if the network should marked as migration network."
            - "C(gluster) - I(true) if the network should marked as gluster network."
    label:
        description:
            - "Name of the label to assign to the network."
        version_added: "2.5"
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create network
- ovirt_networks:
    data_center: mydatacenter
    name: mynetwork
    vlan_tag: 1
    vm_network: true

# Remove network
- ovirt_networks:
    state: absent
    name: mynetwork
'''

RETURN = '''
id:
    description: "ID of the managed network"
    returned: "On success if network is found."
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
network:
    description: "Dictionary of all the network attributes. Network attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/network."
    returned: "On success if network is found."
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


class NetworksModule(BaseModule):

    def build_entity(self):
        return otypes.Network(
            name=self._module.params['name'],
            comment=self._module.params['comment'],
            description=self._module.params['description'],
            data_center=otypes.DataCenter(
                name=self._module.params['data_center'],
            ) if self._module.params['data_center'] else None,
            vlan=otypes.Vlan(
                self._module.params['vlan_tag'],
            ) if self._module.params['vlan_tag'] else None,
            usages=[
                otypes.NetworkUsage.VM if self._module.params['vm_network'] else None
            ] if self._module.params['vm_network'] is not None else None,
            mtu=self._module.params['mtu'],
        )

    def post_create(self, entity):
        self._update_label_assignments(entity)

    def _update_label_assignments(self, entity):
        if self.param('label') is None:
            return

        labels = [lbl.id for lbl in self._connection.follow_link(entity.network_labels)]
        labels_service = self._service.service(entity.id).network_labels_service()
        if not self.param('label') in labels:
            if not self._module.check_mode:
                if labels:
                    labels_service.label_service(labels[0]).remove()
                labels_service.add(
                    label=otypes.NetworkLabel(id=self.param('label'))
                )
            self.changed = True

    def update_check(self, entity):
        self._update_label_assignments(entity)
        return (
            equal(self._module.params.get('comment'), entity.comment) and
            equal(self._module.params.get('description'), entity.description) and
            equal(self._module.params.get('vlan_tag'), getattr(entity.vlan, 'id', None)) and
            equal(self._module.params.get('vm_network'), True if entity.usages else False) and
            equal(self._module.params.get('mtu'), entity.mtu)
        )


class ClusterNetworksModule(BaseModule):

    def __init__(self, network_id, cluster_network, *args, **kwargs):
        super(ClusterNetworksModule, self).__init__(*args, **kwargs)
        self._network_id = network_id
        self._cluster_network = cluster_network

    def build_entity(self):
        return otypes.Network(
            id=self._network_id,
            name=self._module.params['name'],
            required=self._cluster_network.get('required'),
            display=self._cluster_network.get('display'),
            usages=[
                otypes.NetworkUsage(usage)
                for usage in ['display', 'gluster', 'migration']
                if self._cluster_network.get(usage, False)
            ] if (
                self._cluster_network.get('display') is not None or
                self._cluster_network.get('gluster') is not None or
                self._cluster_network.get('migration') is not None
            ) else None,
        )

    def update_check(self, entity):
        return (
            equal(self._cluster_network.get('required'), entity.required) and
            equal(self._cluster_network.get('display'), entity.display) and
            equal(
                sorted([
                    usage
                    for usage in ['display', 'gluster', 'migration']
                    if self._cluster_network.get(usage, False)
                ]),
                sorted([
                    str(usage)
                    for usage in getattr(entity, 'usages', [])
                    # VM + MANAGEMENT is part of root network
                    if usage != otypes.NetworkUsage.VM and usage != otypes.NetworkUsage.MANAGEMENT
                ]),
            )
        )


def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent'],
            default='present',
        ),
        data_center=dict(default=None, required=True),
        name=dict(default=None, required=True),
        description=dict(default=None),
        comment=dict(default=None),
        vlan_tag=dict(default=None, type='int'),
        vm_network=dict(default=None, type='bool'),
        mtu=dict(default=None, type='int'),
        clusters=dict(default=None, type='list'),
        label=dict(default=None),
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
        clusters_service = connection.system_service().clusters_service()
        networks_service = connection.system_service().networks_service()
        networks_module = NetworksModule(
            connection=connection,
            module=module,
            service=networks_service,
        )
        state = module.params['state']
        search_params = {
            'name': module.params['name'],
            'datacenter': module.params['data_center'],
        }
        if state == 'present':
            ret = networks_module.create(search_params=search_params)

            # Update clusters networks:
            if module.params.get('clusters') is not None:
                for param_cluster in module.params.get('clusters'):
                    cluster = search_by_name(clusters_service, param_cluster.get('name'))
                    if cluster is None:
                        raise Exception("Cluster '%s' was not found." % param_cluster.get('name'))
                    cluster_networks_service = clusters_service.service(cluster.id).networks_service()
                    cluster_networks_module = ClusterNetworksModule(
                        network_id=ret['id'],
                        cluster_network=param_cluster,
                        connection=connection,
                        module=module,
                        service=cluster_networks_service,
                    )
                    if param_cluster.get('assigned', True):
                        ret = cluster_networks_module.create()
                    else:
                        ret = cluster_networks_module.remove()

        elif state == 'absent':
            ret = networks_module.remove(search_params=search_params)

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
