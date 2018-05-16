#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_host_package_facts
short_description: Gathers facts about available packages on an ESXi host
description:
- This module can be used to gather facts about available packages and their status on an ESXi host.
version_added: '2.5'
author:
- Abhijeet Kasurde (@Akasurde)
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - Package facts about each ESXi server will be returned for given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - Package facts about this ESXi server will be returned.
    - If C(cluster_name) is not given, this parameter is required.
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Gather facts about all ESXi Host in given Cluster
  vmware_host_package_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
  register: cluster_host_packages

- name: Gather facts about ESXi Host
  vmware_host_package_facts:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
  register: host_packages
'''

RETURN = r'''
hosts_package_facts:
    description:
    - dict with hostname as key and dict with package facts as value
    returned: hosts_package_facts
    type: dict
    sample: { "hosts_package_facts": { "localhost.localdomain": []}}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi


class VmwarePackageManager(PyVmomi):
    def __init__(self, module):
        super(VmwarePackageManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)

    def gather_package_facts(self):
        hosts_facts = {}
        for host in self.hosts:
            host_package_facts = []
            host_pkg_mgr = host.configManager.imageConfigManager
            if host_pkg_mgr:
                pkgs = host_pkg_mgr.FetchSoftwarePackages()
                for pkg in pkgs:
                    host_package_facts.append(dict(name=pkg.name,
                                                   version=pkg.version,
                                                   vendor=pkg.vendor,
                                                   summary=pkg.summary,
                                                   description=pkg.description,
                                                   acceptance_level=pkg.acceptanceLevel,
                                                   maintenance_mode_required=pkg.maintenanceModeRequired,
                                                   creation_date=pkg.creationDate,
                                                   )
                                              )
            hosts_facts[host.name] = host_package_facts
        return hosts_facts


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )

    vmware_host_package_config = VmwarePackageManager(module)
    module.exit_json(changed=False, hosts_package_facts=vmware_host_package_config.gather_package_facts())


if __name__ == "__main__":
    main()
