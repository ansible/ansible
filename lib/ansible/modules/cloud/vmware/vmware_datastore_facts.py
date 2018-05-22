#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Tim Rightnour <thegarbledone@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: vmware_datastore_facts
short_description: Gather facts about datastores available in given vCenter
description:
    - This module can be used to gather facts about datastores in VMWare infrastructure.
    - All values and VMware object names are case sensitive.
version_added: 2.5
author:
    - Tim Rightnour (@garbled1)
notes:
    - Tested on vSphere 5.5, 6.0 and 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
     description:
     - Name of the datastore to match.
     - If set, facts of specific datastores are returned.
     required: False
   datacenter:
     description:
     - Datacenter to search for datastores.
     - This parameter is required, if C(cluster) is not supplied.
     required: False
   cluster:
     description:
     - Cluster to search for datastores.
     - If set, facts of datastores belonging this clusters will be returned.
     - This parameter is required, if C(datacenter) is not supplied.
     required: False
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather facts from standalone ESXi server having datacenter as 'ha-datacenter'
  vmware_datastore_facts:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    datacenter: ha-datacenter
    validate_certs: no
  delegate_to: localhost
  register: facts

- name: Gather facts from datacenter about specific datastore
  vmware_datastore_facts:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    datacenter: DC0
    name: datastore1
    validate_certs: no
  delegate_to: localhost
  register: facts
'''

RETURN = """
datastores:
    description: metadata about the available datastores
    returned: always
    type: list
    sample: [
        {
            "accessible": false,
            "capacity": 42681237504,
            "datastore_cluster": "datacluster0",
            "freeSpace": 39638269952,
            "maintenanceMode": "normal",
            "multipleHostAccess": false,
            "name": "datastore2",
            "provisioned": 12289211488,
            "type": "VMFS",
            "uncommitted": 9246243936,
            "url": "ds:///vmfs/volumes/5a69b18a-c03cd88c-36ae-5254001249ce/"
        },
    ]
"""

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, vmware_argument_spec, get_all_objs,
                                         find_cluster_by_name, get_parent_datacenter)


class PyVmomiCache(object):
    """ This class caches references to objects which are requested multiples times but not modified """
    def __init__(self, content, dc_name=None):
        self.content = content
        self.dc_name = dc_name
        self.clusters = {}
        self.parent_datacenters = {}

    def get_all_objs(self, content, types, confine_to_datacenter=True):
        """ Wrapper around get_all_objs to set datacenter context """
        objects = get_all_objs(content, types)
        if confine_to_datacenter:
            if hasattr(objects, 'items'):
                # resource pools come back as a dictionary
                for k, v in objects.items():
                    parent_dc = get_parent_datacenter(k)
                    if parent_dc.name != self.dc_name:
                        objects.pop(k, None)
            else:
                # everything else should be a list
                objects = [x for x in objects if get_parent_datacenter(x).name == self.dc_name]

        return objects


class PyVmomiHelper(PyVmomi):
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.cache = PyVmomiCache(self.content, dc_name=self.params['datacenter'])

    def lookup_datastore(self):
        datastores = self.cache.get_all_objs(self.content, [vim.Datastore], confine_to_datacenter=True)
        return datastores

    def lookup_datastore_by_cluster(self):
        cluster = find_cluster_by_name(self.content, self.params['cluster'])
        if not cluster:
            self.module.fail_json(msg='Failed to find cluster "%(cluster)s"' % self.params)
        c_dc = cluster.datastore
        return c_dc


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        datacenter=dict(type='str'),
        cluster=dict(type='str')
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[
                               ['cluster', 'datacenter'],
                           ],
                           )
    result = dict(changed=False)

    pyv = PyVmomiHelper(module)

    if module.params['cluster']:
        dxs = pyv.lookup_datastore_by_cluster()
    else:
        dxs = pyv.lookup_datastore()

    datastores = list()
    for ds in dxs:
        summary = ds.summary
        dds = dict()
        dds['accessible'] = summary.accessible
        dds['capacity'] = summary.capacity
        dds['name'] = summary.name
        dds['freeSpace'] = summary.freeSpace
        dds['maintenanceMode'] = summary.maintenanceMode
        dds['multipleHostAccess'] = summary.multipleHostAccess
        dds['type'] = summary.type
        # vcsim does not return uncommitted
        if not summary.uncommitted:
            summary.uncommitted = 0
        dds['uncommitted'] = summary.uncommitted
        dds['url'] = summary.url
        # Calculated values
        dds['provisioned'] = summary.capacity - summary.freeSpace + summary.uncommitted
        dds['datastore_cluster'] = 'N/A'
        if isinstance(ds.parent, vim.StoragePod):
            dds['datastore_cluster'] = ds.parent.name

        if module.params['name']:
            if dds['name'] == module.params['name']:
                datastores.extend([dds])
        else:
            datastores.extend([dds])

    result['datastores'] = datastores

    # found a datastore
    if datastores:
        module.exit_json(**result)
    else:
        msg = "Unable to gather datastore facts"
        if module.params['name']:
            msg += " for %(name)s" % module.params
        msg += " in datacenter %(datacenter)s" % module.params
        module.fail_json(msg=msg)


if __name__ == '__main__':
    main()
