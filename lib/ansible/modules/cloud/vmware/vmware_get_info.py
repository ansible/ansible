#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_get_info
short_description: Gathers facts about various VMware object using REST API
description:
- This module can be used to gather facts about various VMware object using REST APIs.
- This module is based on REST API and uses HTTP API connection plugin for persistent connection.
version_added: '2.9'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5, 6.7
requirements:
- python >= 2.6
options:
  object_type:
    description:
    - Type of VMware object.
    - Valid choices are datacenter, cluster, datastore, folder, host, network,
      resource_pool, virtual_machine, content_library, local_library, subscribed_library, content_type, tag, category.
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
'''

EXAMPLES = r'''
- name: Get Datacenter object information
  vmware_get_info:
    object_type: datacenter
    filters:
      - names: Asia-Datacenter1
  register: datacenter_result

- set_fact:
    datacenter_obj: "{{ datacenter_result.object_info.value[0]['datacenter'] }}"

- name: Get all clusters from Asia-Datacenter1
  vmware_get_info:
    object_type: cluster
    filters:
      - datacenters: "{{ datacenter_obj }}"
  register: clusters_result
'''

RETURN = r'''
object_info:
    description: facts about the given VMware object
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

from ansible.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = dict(
        object_type=dict(type='str', default='datacenter'),
        filters=dict(type='list', default=[]),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    conn = Connection(module._socket_path)

    rest_result = {}
    object_type = module.params['object_type']
    object_type_url_map = dict(
        datacenter=('/vcenter/datacenter', ['folders', 'datacenters', 'names']),
        cluster=('/vcenter/cluster', ['folders', 'datacenters', 'names', 'clusters']),
        datastore=('/vcenter/datastore', ['folders', 'datacenters', 'names', 'datastores', 'types']),
        folder=('/vcenter/folder', ['folders', 'datacenters', 'names', 'parent_folders', 'type']),
        host=('/vcenter/host', ['folders', 'datacenters', 'names', 'hosts', 'clusters', 'connection_states']),
        network=('/vcenter/network', ['folders', 'datacenters', 'names', 'types', 'networks']),
        resource_pool=('/vcenter/resource-pool', ['datacenters', 'names', 'hosts', 'parent_resource_pools', 'clusters', 'resource_pools']),
        virtual_machine=('/vcenter/vm', ['folders', 'datacenters', 'names', 'hosts', 'power_states', 'clusters', 'resource_pools', 'vms']),
        content_library=('/com/vmware/content/library', []),
        local_library=('/com/vmware/content/local-library', []),
        subscribed_library=('/com/vmware/content/subscribed-library', []),
        content_type=('/com/vmware/content/type', []),
        category=('/com/vmware/cis/tagging/category', []),
        tag=('/com/vmware/cis/tagging/tag', []),
    )

    try:
        object_url = '/rest' + object_type_url_map[object_type][0]
    except KeyError as e:
        module.fail_json(msg='Please specify correct object type to get '
                             'information, valid choices are [%s].' % ", ".join(list(object_type_url_map.keys())))

    filters = module.params.get('filters')
    if filters:
        first = True
        for filter in filters:
            for key in list(filter.keys()):
                lower_key = key.lower()
                if lower_key not in object_type_url_map[object_type][1]:
                    # Check if filter is valid for current object type or not
                    continue
                if not first:
                    object_url += '&'
                else:
                    object_url += '?'
                    first = False
                # Escape characters
                if '/' in filter[key]:
                    filter[key].replace('/', '%2F')
                object_url += 'filter.%s=%s' % (lower_key, filter[key])

    return_code, response = conn.send_request(object_url, {}, method='GET')

    if return_code == 200:
        rest_result['object_info'] = response
        module.exit_json(**rest_result)
    elif return_code == 401:
        module.fail_json(msg="Unable to authenticate. Provided credentials are not valid.")
    else:
        try:
            msg = response['value']['messages'][0]['default_message']
        except (KeyError, TypeError) as e:
            msg = "Unable to find the %s object specified due to %s" % (object_type, response)
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
