#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
# Copyright: (c) 2019, Paul Knight <paul.knight@delaware.gov>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: vmware_core_info
short_description: Gathers info about various VMware inventory objects using REST API
description:
- This module can be used to gather information about various VMware inventory objects.
- This module is based on REST API and uses httpapi connection plugin for persistent connection.
version_added: '2.10'
author:
- Abhijeet Kasurde (@Akasurde)
- Paul Knight (@n3pjk)
notes:
- Tested on vSphere 6.7
requirements:
- python >= 2.6
options:
  object_type:
    description:
    - Type of VMware object.
    - Valid choices are datacenter, cluster, datastore, folder, host,
      network, resource_pool, virtual_machine, content_library,
      local_library, subscribed_library, content_type, tag, category.
    type: str
    default: datacenter
  filters:
    description:
    - A list of filters to find the given object.
    - Valid filters for datacenter object type - folders, datacenters, names.
    - Valid filters for cluster object type - folders, datacenters, names, clusters.
    - Valid filters for datastore object type - folders, datacenters, names, datastores, types.
    - Valid filters for folder object type - folders, parent_folders, names, datacenters, type.
    - Valid filters for host object type - folders, hosts, names, datacenters, clusters, connection_states.
    - Valid filters for network object type - folders, types, names, datacenters, networks.
    - Valid filters for resource_pool object type - resource_pools, parent_resource_pools, names, datacenters, hosts, clusters.
    - Valid filters for virtual_machine object type - folders, resource_pools, power_states, vms, names, datacenters, hosts, clusters.
    - content_library, local_library, subscribed_library, content_type, tag, category does not take any filters.
    default: []
    type: list
extends_documentation_fragment: VmwareRestModule_filters.documentation
'''

EXAMPLES = r'''
- name: Get All VM without any filters
  block:
  - name: Get VMs
    vmware_core_info:
      object_type: "{{ object_type }}"
    register: vm_result

  - assert:
      that:
      - vm_result[object_type].value | length > 0
  vars:
    object_type: vm

- name: Get all clusters from Asia-Datacenter1
  vmware_core_info:
    object_type: cluster
    filters:
      - datacenters: "{{ datacenter_obj }}"
  register: clusters_result
'''

RETURN = r'''
object_info:
    description: information about the given VMware object
    returned: always
    type: dict
    sample: {
        "value": [
            {
                "cluster": "domain-c42",
                "drs_enabled": false,
                "ha_enabled": false,
                "name": "Asia-Cluster1"
            }
        ]
    }
'''

from ansible.module_utils.vmware_httpapi.VmwareRestModule import VmwareRestModule


def main():
    argument_spec = VmwareRestModule.create_argument_spec(use_filters=True)
    argument_spec.update(
        object_type=dict(type='str', default='datacenter'),
    )

    module = VmwareRestModule(argument_spec=argument_spec,
                              supports_check_mode=True,
                              use_object_handler=True)
    object_type = module.params['object_type']

    url = module.get_url_with_filter(object_type)

    module.get(url=url, key=object_type)
    module.exit()


if __name__ == '__main__':
    main()
