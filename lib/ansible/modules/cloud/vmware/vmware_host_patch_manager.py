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
module: vmware_host_patch_manager
short_description: Manage patches on an ESXi host
description:
- This module can be used to install, uninstall patches on an ESXi host.
version_added: '2.9'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.7
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - Manage patches on all the ESXi hostsystems under the cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname.
    - Manage patches on this ESXi hostsystem.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
  vibs:
    description:
    - A List of VIBs to operate on.
    - If C(state) is C(present), C(meta_url) and C(vib_url) is required for the given VIB. C(name) is optional.
    - If C(state) is C(absent), C(name) is required for the given VIB. C(meta_url) and C(vib_url) is optional.
    type: list
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Install patches on all ESXi Host in given Cluster
  vmware_host_patch_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
    vibs:
      - meta_url: 'http://192.168.56.1/metadata.zip'
        vib_url: 'http://192.168.56.1/vib20/ata-pata-amd/VMW_bootbank_ata-pata-amd_0.3.10-3vmw.670.0.0.8169922.vib'
      - meta_url: 'http://192.168.56.1/metadata.zip'
        vib_url: 'http://localhost/vib20/esx-update/VMware_bootbank_esx-update_6.7.0-1.44.12986307.vib'
  delegate_to: localhost

- name: Install patches on the given ESXi Host
  vmware_host_patch_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    vibs:
      - meta_url: 'http://192.168.56.1/metadata.zip'
        vib_url: 'http://192.168.56.1/vib20/ata-pata-amd/VMW_bootbank_ata-pata-amd_0.3.10-3vmw.670.0.0.8169922.vib'
      - meta_url: 'http://192.168.56.1/metadata.zip'
        vib_url: 'http://localhost/vib20/esx-update/VMware_bootbank_esx-update_6.7.0-1.44.12986307.vib'
  delegate_to: localhost

- name: Uninstall patches on all ESXi Host in given Cluster
  vmware_host_patch_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
    vibs:
      - name: scsi-megaraid-perc9
      - name: scsi-mpt3sas
    delegate_to: localhost

- name: Uninstall patches on the given ESXi Host
  vmware_host_patch_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    vibs:
      - name: scsi-megaraid-perc9
      - name: scsi-mpt3sas
  delegate_to: localhost
'''

RETURN = r'''
patch_results:
    description:
    - dict with hostname as key and dict with package facts as value
    type: dict
    sample: {
        "localhost.localdomain": {
            "changed": false,
            "info": "",
            "meta_url": "http://192.168.56.1",
            "vib_url": "http://192.168.56.1/vib20/ata-pata-amd/VMW_bootbank_ata-pata-amd_0.3.10-3vmw.670.0.0.8169922.vib"
        },
    }

'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi, wait_for_task


class VmwarePatchManager(PyVmomi):
    def __init__(self, module):
        super(VmwarePatchManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def ensure(self):
        state = self.params.get('state')
        patches = self.params.get('vibs')

        if not patches:
            self.module.fail_json(msg="VIB information is required to perform %s operation" % state)

        change_list = []
        results = dict()

        if state == 'present':
            for patch in patches:
                meta_url = patch.get('meta_url')
                vib_url = patch.get('vib_url')
                if not all([meta_url, vib_url]):
                    self.module.fail_json(msg="meta_url and vib_url is required when installing a VIB.")

                for host in self.hosts:
                    patch_manager = host.configManager.patchManager
                    if not patch_manager:
                        self.module.fail_json(msg="Unable to get patch manager for host %s" % host.name)

                    if not self.module.check_mode:
                        task = patch_manager.InstallHostPatchV2_Task(metaUrls=meta_url, vibUrls=vib_url)
                        changed, info = wait_for_task(task)

                        if hasattr(info, 'xmlResult') and ('Host was not updated' in info.xmlResult or 'Failed to download VIB' in info.xmlResult):
                            changed = False

                        if changed:
                            change_list.append(patch)
                    else:
                        changed = True
                        change_list = [True]

                    if host.name not in results:
                        results[host.name] = []

                    results[host.name].append(dict(changed=changed, vib_url=vib_url, meta_url=meta_url, info=str(info.xmlResult)))

            if change_list:
                self.module.exit_json(changed=True, patch_results=results)
            else:
                self.module.exit_json(changed=False, patch_results=results)
        elif state == 'absent':
            for patch in patches:
                name = patch.get('name')
                if not name:
                    self.module.fail_json(msg="name is required while removing a VIB")

                for host in self.hosts:
                    patch_manager = host.configManager.patchManager
                    if not patch_manager:
                        self.module.fail_json(msg="Unable to get patch manager for host %s" % host.name)

                    if not self.module.check_mode:
                        task = patch_manager.UninstallHostPatch_Task([name])

                        changed, info = wait_for_task(task)

                        if changed:
                            change_list.append(patch)
                    else:
                        changed = True
                        change_list = [True]

                    if host.name not in results:
                        results[host.name] = []

                    results[host.name].append(dict(changed=changed, name=name, info=str(info.xmlResult)))

            if change_list:
                self.module.exit_json(changed=True, patch_results=results)
            else:
                self.module.exit_json(changed=False, patch_results=results)
        else:
            self.module.exit_json(changed=False, patch_results=results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        vibs=dict(type='list', default=[]),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ],
        supports_check_mode=True,
    )

    vmware_host_patch_config = VmwarePatchManager(module)
    module.exit_json(changed=False, hosts_patch_facts=vmware_host_patch_config.ensure())


if __name__ == "__main__":
    main()
