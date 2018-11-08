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
     aliases: ['datacenter_name']
   cluster:
     description:
     - Cluster to search for datastores.
     - If set, facts of datastores belonging this clusters will be returned.
     - This parameter is required, if C(datacenter) is not supplied.
     required: False
   gather_nfs_mount_info:
    description:
    - Gather mount information of NFS datastores.
    - Disabled per default because this slows down the execution if you have a lot of datastores.
    type: bool
    default: false
    version_added: 2.8
   gather_vmfs_mount_info:
    description:
    - Gather mount information of VMFS datastores.
    - Disabled per default because this slows down the execution if you have a lot of datastores.
    type: bool
    default: false
    version_added: 2.8
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather facts from standalone ESXi server having datacenter as 'ha-datacenter'
  vmware_datastore_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    validate_certs: no
  delegate_to: localhost
  register: facts

- name: Gather facts from datacenter about specific datastore
  vmware_datastore_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: '{{ datacenter_name }}'
    name: datastore1
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
            "url": "ds:///vmfs/volumes/5a69b18a-c03cd88c-36ae-5254001249ce/",
            "vmfs_blockSize": 1024,
            "vmfs_uuid": "5a69b18a-c03cd88c-36ae-5254001249ce",
            "vmfs_version": "6.81"
        },
        {
            "accessible": true,
            "capacity": 5497558138880,
            "datastore_cluster": "datacluster0",
            "freeSpace": 4279000641536,
            "maintenanceMode": "normal",
            "multipleHostAccess": true,
            "name": "datastore3",
            "nfs_path": "/vol/datastore3",
            "nfs_server": "nfs_server1",
            "provisioned": 1708109410304,
            "type": "NFS",
            "uncommitted": 489551912960,
            "url": "ds:///vmfs/volumes/420b3e73-67070776/"
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


class VMwareHostDatastore(PyVmomi):
    """ This class populates the datastore list """
    def __init__(self, module):
        super(VMwareHostDatastore, self).__init__(module)
        self.gather_nfs_mount_info = self.module.params['gather_nfs_mount_info']
        self.gather_vmfs_mount_info = self.module.params['gather_vmfs_mount_info']

    def check_datastore_host(self, esxi_host, datastore):
        """ Get all datastores of specified ESXi host """
        esxi = self.find_hostsystem_by_name(esxi_host)
        if esxi is None:
            self.module.fail_json(msg="Failed to find ESXi hostname %s " % esxi_host)
        storage_system = esxi.configManager.storageSystem
        host_file_sys_vol_mount_info = storage_system.fileSystemVolumeInfo.mountInfo
        for host_mount_info in host_file_sys_vol_mount_info:
            if host_mount_info.volume.name == datastore:
                return host_mount_info
        return None

    def build_datastore_list(self, datastore_list):
        """ Build list with datastores """
        datastores = list()
        for datastore in datastore_list:
            summary = datastore.summary
            datastore_summary = dict()
            datastore_summary['accessible'] = summary.accessible
            datastore_summary['capacity'] = summary.capacity
            datastore_summary['name'] = summary.name
            datastore_summary['freeSpace'] = summary.freeSpace
            datastore_summary['maintenanceMode'] = summary.maintenanceMode
            datastore_summary['multipleHostAccess'] = summary.multipleHostAccess
            datastore_summary['type'] = summary.type
            if self.gather_nfs_mount_info or self.gather_vmfs_mount_info:
                if self.gather_nfs_mount_info and summary.type.startswith("NFS"):
                    # get mount info from the first ESXi host attached to this NFS datastore
                    host_mount_info = self.check_datastore_host(summary.datastore.host[0].key.name, summary.name)
                    datastore_summary['nfs_server'] = host_mount_info.volume.remoteHost
                    datastore_summary['nfs_path'] = host_mount_info.volume.remotePath
                if self.gather_vmfs_mount_info and summary.type == "VMFS":
                    # get mount info from the first ESXi host attached to this VMFS datastore
                    host_mount_info = self.check_datastore_host(summary.datastore.host[0].key.name, summary.name)
                    datastore_summary['vmfs_blockSize'] = host_mount_info.volume.blockSize
                    datastore_summary['vmfs_version'] = host_mount_info.volume.version
                    datastore_summary['vmfs_uuid'] = host_mount_info.volume.uuid
            # vcsim does not return uncommitted
            if not summary.uncommitted:
                summary.uncommitted = 0
            datastore_summary['uncommitted'] = summary.uncommitted
            datastore_summary['url'] = summary.url
            # Calculated values
            datastore_summary['provisioned'] = summary.capacity - summary.freeSpace + summary.uncommitted
            datastore_summary['datastore_cluster'] = 'N/A'
            if isinstance(datastore.parent, vim.StoragePod):
                datastore_summary['datastore_cluster'] = datastore.parent.name

            if self.module.params['name']:
                if datastore_summary['name'] == self.module.params['name']:
                    datastores.extend([datastore_summary])
            else:
                datastores.extend([datastore_summary])

        return datastores


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
    """ This class gets datastores """
    def __init__(self, module):
        super(PyVmomiHelper, self).__init__(module)
        self.cache = PyVmomiCache(self.content, dc_name=self.params['datacenter'])

    def lookup_datastore(self):
        """ Get datastore(s) per ESXi host or vCenter server """
        datastores = self.cache.get_all_objs(self.content, [vim.Datastore], confine_to_datacenter=True)
        return datastores

    def lookup_datastore_by_cluster(self):
        """ Get datastore(s) per cluster """
        cluster = find_cluster_by_name(self.content, self.params['cluster'])
        if not cluster:
            self.module.fail_json(msg='Failed to find cluster "%(cluster)s"' % self.params)
        c_dc = cluster.datastore
        return c_dc


def main():
    """ Main """
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        datacenter=dict(type='str', aliases=['datacenter_name']),
        cluster=dict(type='str'),
        gather_nfs_mount_info=dict(type='bool', default=False),
        gather_vmfs_mount_info=dict(type='bool', default=False)
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[
                               ['cluster', 'datacenter'],
                           ],
                           supports_check_mode=True
                           )
    result = dict(changed=False)

    pyv = PyVmomiHelper(module)

    if module.params['cluster']:
        dxs = pyv.lookup_datastore_by_cluster()
    else:
        dxs = pyv.lookup_datastore()

    vmware_host_datastore = VMwareHostDatastore(module)
    datastores = vmware_host_datastore.build_datastore_list(dxs)

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
