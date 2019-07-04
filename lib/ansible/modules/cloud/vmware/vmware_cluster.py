#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Joseph Callen <jcallen () csc.com>
# Copyright: (c) 2018, Ansible Project
#
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
module: vmware_cluster
short_description: Manage VMware vSphere clusters
description:
    - This module can be used to add and remove VMware vSphere clusters.
    - All values and VMware object names are case sensitive.
version_added: '2.0'
author:
- Joseph Callen (@jcpowermac)
- Abhijeet Kasurde (@Akasurde)
requirements:
    - Tested on ESXi 5.5 and 6.5.
    - PyVmomi installed.
options:
    cluster_name:
      description:
      - The name of the cluster to be managed.
      type: str
      required: yes
    datacenter:
      description:
      - The name of the datacenter.
      type: str
      required: yes
      aliases: [ datacenter_name ]
    state:
      description:
      - Create C(present) or remove C(absent) a VMware vSphere cluster.
      choices: [ absent, present ]
      default: present
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r"""
- name: Create Cluster
  vmware_cluster:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    datacenter_name: datacenter
    cluster_name: cluster
  delegate_to: localhost

- name: Delete Cluster
  vmware_cluster:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    datacenter_name: datacenter
    cluster_name: cluster
    state: absent
"""

RETURN = r"""#
"""

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import (PyVmomi, TaskError, find_datacenter_by_name,
                                         vmware_argument_spec, wait_for_task)
from ansible.module_utils._text import to_native


class VMwareCluster(PyVmomi):
    def __init__(self, module):
        super(VMwareCluster, self).__init__(module)
        self.cluster_name = module.params['cluster_name']
        self.datacenter_name = module.params['datacenter']
        self.desired_state = module.params['state']
        self.datacenter = None
        self.cluster = None

    def ensure_state(self):
        """
        Manage cluster state
        """
        cluster_state = self.get_cluster_state()
        if cluster_state == "absent" and self.desired_state == "present":
            self.create_cluster()
        elif cluster_state == "present" and self.desired_state == "absent":
            self.destroy_cluster()
        else:
            self.module.exit_json(changed=False)

    def create_cluster(self):
        """
        Create cluster with given configuration
        """
        try:
            cluster_config_spec = vim.cluster.ConfigSpecEx()
            if not self.module.check_mode:
                self.datacenter.hostFolder.CreateClusterEx(self.cluster_name, cluster_config_spec)
            self.module.exit_json(changed=True)
        except vim.fault.DuplicateName:
            # To match other vmware_* modules
            pass
        except vmodl.fault.InvalidArgument as invalid_args:
            self.module.fail_json(msg="Cluster configuration specification"
                                      " parameter is invalid : %s" % to_native(invalid_args.msg))
        except vim.fault.InvalidName as invalid_name:
            self.module.fail_json(msg="'%s' is an invalid name for a"
                                      " cluster : %s" % (self.cluster_name,
                                                         to_native(invalid_name.msg)))
        except vmodl.fault.NotSupported as not_supported:
            # This should never happen
            self.module.fail_json(msg="Trying to create a cluster on an incorrect"
                                      " folder object : %s" % to_native(not_supported.msg))
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            # This should never happen either
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to create cluster"
                                      " due to generic exception %s" % to_native(generic_exc))

    def destroy_cluster(self):
        """
        Destroy cluster
        """
        changed, result = False, None

        try:
            if not self.module.check_mode:
                task = self.cluster.Destroy_Task()
                changed, result = wait_for_task(task)
            self.module.exit_json(changed=changed, result=result)
        except vim.fault.VimFault as vim_fault:
            self.module.fail_json(msg=to_native(vim_fault.msg))
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to destroy cluster"
                                      " due to generic exception %s" % to_native(generic_exc))

    def get_cluster_state(self):
        """
        Check cluster configuration
        Returns: 'present' if cluster exists, else 'absent'

        """
        try:
            self.datacenter = find_datacenter_by_name(self.content, self.datacenter_name)
            if self.datacenter is None:
                self.module.fail_json(msg="Datacenter %s does not exist." % self.datacenter_name)
            self.cluster = self.find_cluster_by_name(cluster_name=self.cluster_name)

            if self.cluster is None:
                return 'absent'

            return 'present'
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed to check configuration"
                                      " due to generic exception %s" % to_native(generic_exc))


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(dict(
        cluster_name=dict(type='str', required=True),
        datacenter=dict(type='str', required=True, aliases=['datacenter_name']),
        state=dict(type='str',
                   default='present',
                   choices=['absent', 'present']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    vmware_cluster = VMwareCluster(module)
    vmware_cluster.ensure_state()


if __name__ == '__main__':
    main()
