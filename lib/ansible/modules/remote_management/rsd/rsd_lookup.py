#!/usr/bin/python
# -*- coding: utf-8 -*-

#######################################################
# Copyright (c) 2019 Intel Corporation. All rights reserved.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# Authors:
#   - Radoslaw Kuschel - <radoslaw.kuschel@intel.com>
#######################################################

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: rsd_lookup

short_description: Displays information about RSD composed node.

version_added: "2.10"

description:
    - 'rsd_lookup show information about Rack Scale Design composed nodes.'
    - 'Information displayed cover following, general information about node,
      information about remote resources attached to the node and available
      resources for attachment.'
    - 'Module supports information to be dispayed in full details or generic
      format for better readability. Filtering is also supported to retrieve
      specific information about composed node.'
    - 'Module was tested with RSD version 2.3 and 2.4'

options:
    node_info:
        description:
            - This option is used to display information about composed node.
            - C(power), is used to show power state of the node and supported
              power states available.
            - C(basic), is used to show generic information about node.
            - C(boot), is used to show information about current and available
              booting options of the node.
            - C(links), is used to displays resources URIs available under
              'Links' section.
            - C(all), is used to show all details about composed node,
              including above information.
        required: false
        type: str
        choices: [power, basic, boot, links, all]
    attached_resources:
        description:
            - This option show information about attached resources to
              the node. It contains two sub-options, resource to define
              type of resource to be shown and details to display
              information in generic or detailed format.
        type: dict
        required: false
        suboptions:
            resource:
                description:
                    - this option is used to specify resource type to be
                      displayed.
                    - C(volumes), is used to show information about
                      attached volumes.
                    - C(drives), is used to show information about
                      attached drives.
                    - C(endpoints), is used to show information about
                      attached endpoints.
                    - C(processors), is used to show information about
                      attached processors.
                    - C(all), is used to show information about all
                      resources that are attached to the node.
                type: 'str'
                required: false
                choices: ['all', 'volumes', 'drives', 'endpoints',
                          'processors']
                default: 'all'
            details:
                description:
                    - This option is used to define if resource
                      information should be shown in detailed
                      or generic format.
                    - true, is used to display resource information
                      in detailed format.
                    - false, is used to display information in generic
                      format.
                type: bool
                default: true
    available_resources:
        description:
            - This option show information about available resources
              which could be attached to the node. It contains two
              sub-options, resource to define type of resource
              to be shown and details which defines if information
              should be displayed in detailed or generic format.
        type: dict
        required: false
        suboptions:
            resource:
                description:
                    - this option is used to specify resource type to be
                      displayed.
                    - C(volumes), is used to show information about
                      attached volumes.
                    - C(drives), is used to show information about
                      attached drives.
                    - C(endpoints), is used to show information about
                      attached endpoints.
                    - C(processors), is used to show information about
                      attached processors.
                    - C(all), is used to show information about all
                      resources which are attached to the node.
                type: 'str'
                required: false
                choices: ['all', 'volumes', 'drives', 'endpoints',
                          'processors']
                default: 'all'
            details:
                description:
                    - This option is used to define if resource
                      information should be shown in detailed
                      or generic format.
                    - true, is used to display resource information
                      in detailed format.
                    - false, is used to display information in generic
                      format.
                type: bool
                default: true

extends_documentation_fragment:
    - rsd

author:
    - Radoslaw Kuschel (@radoslawKuschel)
'''
EXAMPLES = '''
- name: Details of all resources available for attachment for node with id 1
  rsd_lookup:
    id:
      value: 1
    available_resources:
      resource: all

- name: Volumes available for attachment for node with id 1
  rsd_lookup:
    id:
      value: 1
    available_resources:
      resource: volumes
  register: output
- name: Get URI of volumes with capacity equal to or greater than 2 GiB.
  debug:
    msg: "{{ output | json_query('node.available_resources.Volumes[].*[] | [?CapacityBytes>=`2147483648`].URI') }}"

- name: Volumes available for attachment for node with id 1
  rsd_lookup:
    id:
      value: 1
    available_resources:
      resource: volumes
  register: output
- name: Get URI of first non-bootable volume.
  debug:
    msg: "{{ output | json_query('node.available_resources.Volumes[].*[] | [?Bootable==`false`].URI | [0] ') }}"

- name: Volumes available for attachment for node with id 1
  rsd_lookup:
    id:
      value: 1
    available_resources:
      resource: volumes
  register: output
- name: Get URI of non-bootable volumes with capacity equal to or greater than 2 GiB.
  debug:
    msg: "{{ output | json_query('node.available_resources.Volumes[].*[] | [?Bootable==`false` && CapacityBytes>=`2147483648`].URI') }}"

- name: Details of Volumes attached to node with id 1
  rsd_lookup:
    id:
      value: 1
    attached_resources:
      resource: volumes

- name: Show power state and power options of node with id 1
  rsd_lookup:
    id:
      value: 1
    node_info: power

- name: Show attached/available drives in generic format of node with id 1
  rsd_lookup:
    id:
      value: 1
    attached_resources:
      resource: drives
      details: false
    available_resources:
      resource: drives
      details: false
'''

RETURN = '''
---
node:
    description: Results depends on chosen option
    returned: always
    type: dict
'''

from ansible.module_utils.remote_management.rsd.rsd_common import RSD


class RsdNodeLookup(RSD):

    def __init__(self):
        argument_spec = dict(
            node_info=dict(
                type='str',
                required=False,
                choices=['all',
                         'basic',
                         'boot',
                         'links',
                         'power']
            ),
            attached_resources=dict(
                type='dict',
                required=False,
                options=dict(
                    resource=dict(
                        type='str',
                        choices=['all',
                                 'volumes',
                                 'drives',
                                 'endpoints',
                                 'processors'],
                        default='all'
                    ),
                    details=dict(
                        type='bool',
                        default=True
                    )
                )
            ),
            available_resources=dict(
                type='dict',
                required=False,
                options=dict(
                    resource=dict(
                        type='str',
                        choices=['all',
                                 'volumes',
                                 'drives',
                                 'endpoints',
                                 'processors'],
                        default='all'
                    ),
                    details=dict(
                        type='bool',
                        default=True
                    )
                )
            ),
        )

        super(RsdNodeLookup, self).__init__(argument_spec, False)

    def _get_resource_type(self, res_uri):
        return res_uri.split("/")[5]

    def _get_volume_resources(self, details, vol_uri):
        volume_info = dict()
        volume = self._get_volume(vol_uri)

        if details is True:

            volume_info.update({
                vol_uri: volume.json})

        else:
            volume_info.update({
                vol_uri: {
                    'Id': volume.identity,
                    'DurableName': volume.identifiers[0].durable_name,
                    'URI': vol_uri,
                    'Name': volume.name,
                    'Description': volume.description,
                    'Bootable': volume.bootable,
                    'CapacityBytes': volume.capacity_bytes}})

        return volume_info

    def _get_drive_resources(self, details, drive_uri):
        drive_info = dict()
        drive = self._get_drive(drive_uri)

        if details is True:

            drive_info.update({
                drive_uri: drive.json})
        else:

            drive_info.update({
                drive_uri: {
                    'Id': drive.identity,
                    'DurableName': drive.identifiers[0].durable_name,
                    'URI': drive_uri,
                    'Name': drive.name,
                    'Description': drive.description,
                    'Protocol': drive.protocol,
                    'CapacityBytes': drive.capacity_bytes}})

        return drive_info

    def _get_endpoint_info(self, details, endpt_uri):
        endpoint_info = dict()
        endpoint = self._get_endpoint(endpt_uri)

        if details is True:

            endpoint_info.update({
                endpt_uri: endpoint.json})

        else:

            endpoint_info.update({
                endpt_uri: {
                    'Id': endpoint.identity,
                    'URI': endpt_uri,
                    'Name': endpoint.name,
                    'Description': endpoint.description,
                    'ConnectedEntities': {
                        'Type': [et.entity_type for et in
                                 endpoint.connected_entities],
                        'Link': [el.entity_link for el in
                                 endpoint.connected_entities]}}})

        return endpoint_info

    def _get_processors_resources(self, details, proc_uri):
        processor_info = dict()
        processor = self._get_processor(proc_uri)
        fpga = processor.oem.intel_rackscale.fpga

        if details is True:

            processor_info.update({
                proc_uri: processor.json})

        else:

            processor_info.update({
                proc_uri: {
                    'Id': processor.identity,
                    'URI': proc_uri,
                    'Name': processor.name,
                    'Description': processor.description,
                    'ProcessorType': processor.processor_type,
                    'Socket': processor.socket,
                    'Oem': {
                        'Intel_RackScale': {
                            'FPGA': {
                                'Type': fpga.fpga_type,
                                'Model': fpga.fpga_model,
                                'ReconfigurationSlots':
                                    fpga.reconfiguration_slots}}}}})

        return processor_info

    def _get_node_resources(self, details, res_param, resources):
        res_inf = dict()

        for res_uri in resources:

            res_type = self._get_resource_type(res_uri)

            if res_type.lower() == res_param or res_param == 'all':

                if res_type not in res_inf:
                    res_inf[res_type] = []

                if res_type == 'Volumes':
                    res_inf['Volumes'].append(
                        self._get_volume_resources(details, res_uri))

                elif res_type == 'Drives':
                    res_inf['Drives'].append(
                        self._get_drive_resources(details, res_uri))

                elif res_type == 'Endpoints':
                    res_inf['Endpoints'].append(
                        self._get_endpoint_info(details, res_uri))

                elif res_type == 'Processors':
                    res_inf['Processors'].append(
                        self._get_processors_resources(details, res_uri))

        return res_inf

    def _get_node_basic_info(self, node, system):
        basic_info = dict()
        basic_info = {
            "Name": node.name,
            "Id": node.identity,
            "UUID": node.uuid,
            "ComposedNodeState": node.composed_node_state,
            "Status": node.status,
            "ClearOptaneDCPersistentMemoryOnDelete":
                node.persistent_memory_operation_on_delete,
            "ClearTPMOnDelete": node.clear_tpm_on_delete,
            "Memory": system.memory_summary,
            "Processor": system.processor_summary,
            "HostingRoles": system.hosting_roles}

        return basic_info

    def _get_node_boot_info(self, node):
        boot_info = dict()
        boot_info['Boot'] = node.boot
        return boot_info

    def _get_node_power_info(self, node):
        power_info = dict()
        power_info["Power"] = {
            "PowerState": node.power_state,
            "AllowableValues": node.get_allowed_reset_node_values()}

        return power_info

    def _get_node_link_info(self, node):
        link_info = dict()
        link_info["Links"] = node.links

        return link_info

    def _get_node_info(self, node, system, params):
        node_info = dict()

        if 'basic' in params['node_info']:
            node_info.update(self._get_node_basic_info(node, system))
        elif 'boot' in params['node_info']:
            node_info.update(self._get_node_boot_info(node))

        elif 'links' in params['node_info']:
            node_info.update(self._get_node_link_info(node))

        elif 'power' in params['node_info']:
            node_info.update(self._get_node_power_info(node))

        elif 'all' in params['node_info']:
            node_info.update(node.json)

        return node_info

    def _collect_return_info(self, node, system, params):
        node_inf = dict()

        if params['node_info']:
            node_inf.update(self._get_node_info(node, system, params))

        if params['attached_resources']:
            details = params['attached_resources']['details']
            res_type = params['attached_resources']['resource']
            resources = node.get_allowed_detach_endpoints()
            node_inf['Attached_resources'] = \
                self._get_node_resources(details, res_type, resources)

        if params['available_resources']:
            details = params['available_resources']['details']
            res_type = params['available_resources']['resource']
            resources = node.get_allowed_attach_endpoints()
            node_inf['available_resources'] = \
                self._get_node_resources(details, res_type, resources)

        self.module.exit_json(changed=False, node=node_inf)

    def run(self):
        node = self._get_node()
        params = self.module.params
        system = self._get_system(node.links.computer_system)
        self._collect_return_info(node, system, params)


def main():
    lookup = RsdNodeLookup()
    lookup.run()


if __name__ == '__main__':
    main()
