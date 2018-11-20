#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Kotte <christian.kotte@gmx.de>
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
module: vmware_host_ipv6
short_description: Enables/Disables IPv6 support for an ESXi host system
description:
- This module can be used to enable or disable IPv6 support for ESXi host systems in given vCenter infrastructure.
- It also checks if the host needs to be restarted.
version_added: 2.8
author:
- Christian Kotte (@ckotte) <christian.kotte@gmx.de>
notes:
- Tested on vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  state:
     description:
        - Enable or disable IPv6 support.
        - You need to reboot the ESXi host if you change the configuration.
     type: str
     choices: [ enabled, disabled ]
     default: 'enabled'
  esxi_hostname:
    description:
    - Name of the host system to work with.
    - This is required parameter if C(cluster_name) is not specified.
    type: str
  cluster_name:
    description:
    - Name of the cluster from which all host systems will be used.
    - This is required parameter if C(esxi_hostname) is not specified.
    type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Enable IPv6 for an host system
  vmware_host_ipv6:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: enabled
    validate_certs: no
  delegate_to: localhost

- name: Disable IPv6 for an host system
  vmware_host_ipv6:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    state: disabled
    validate_certs: no
  delegate_to: localhost

- name: Disable IPv6 for all host systems from cluster
  vmware_host_ipv6:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: '{{ cluster_name }}'
    state: disabled
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
result:
    description: metadata about host system's IPv6 configuration
    returned: always
    type: dict
    sample: {
        "esxi01": {
            "changed": false,
            "msg": "IPv6 is already enabled and active for host 'esxi01'",
        },
    }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VmwareHostIPv6(PyVmomi):
    """Class to manage IPv6 for an ESXi host system"""
    def __init__(self, module):
        super(VmwareHostIPv6, self).__init__(module)
        cluster_name = self.params.get('cluster_name')
        esxi_host_name = self.params.get('esxi_hostname')
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        if not self.hosts:
            self.module.fail_json(msg="Failed to find host system with given configuration.")

    def ensure(self):
        """Manage IPv6 for an ESXi host system"""
        results = dict(changed=False, result=dict())
        desired_state = self.module.params['state']

        host_change_list = []
        for host in self.hosts:
            changed = False
            results['result'][host.name] = dict(msg='')

            host_network_system = host.configManager.networkSystem
            host_network_info = host_network_system.networkInfo

            if desired_state == 'enabled':
                # Don't do anything if IPv6 is already enabled
                if host_network_info.atBootIpV6Enabled:
                    if host_network_info.ipV6Enabled:
                        results['result'][host.name]['msg'] = "IPv6 is already enabled and active for host '%s'" % \
                                                              host.name
                    if not host_network_info.ipV6Enabled:
                        changed = True
                        results['result'][host.name]['msg'] = ("IPv6 is already enabled for host '%s', but a reboot"
                                                               " is required!" % host.name)
                # Enable IPv6
                else:
                    if not self.module.check_mode:
                        try:
                            config = vim.host.NetworkConfig()
                            config.ipV6Enabled = True
                            host_network_system.UpdateNetworkConfig(config, "modify")
                            changed = True
                            results['result'][host.name]['changed'] = True
                            results['result'][host.name]['msg'] = "IPv6 enabled for host '%s'" % host.name
                        except (vim.fault.AlreadyExists, vim.fault.NotFound):
                            self.module.fail_json(msg="Network entity specified in the configuration for host '%s'"
                                                  " already exists" % host.name)
                        except vmodl.fault.InvalidArgument as invalid_argument:
                            self.module.fail_json(msg="Invalid parameter specified for host '%s' : %s" %
                                                  (host.name, to_native(invalid_argument.msg)))
                        except vim.fault.HostConfigFault as config_fault:
                            self.module.fail_json(msg="Failed to enable IPv6 for host '%s' due to : %s" %
                                                  (host.name, to_native(config_fault.msg)))
                        except vmodl.fault.NotSupported as not_supported:
                            self.module.fail_json(msg="Failed to enable IPv6 for host '%s' due to : %s" %
                                                  (host.name, to_native(not_supported.msg)))
                        except (vmodl.RuntimeFault, vmodl.MethodFault) as runtime_fault:
                            self.module.fail_json(msg="Failed to enable IPv6 for host '%s' due to : %s" %
                                                  (host.name, to_native(runtime_fault.msg)))
                    else:
                        changed = True
                        results['result'][host.name]['changed'] = True
                        results['result'][host.name]['msg'] = "IPv6 will be enabled for host '%s'" % host.name
            elif desired_state == 'disabled':
                # Don't do anything if IPv6 is already disabled
                if not host_network_info.atBootIpV6Enabled:
                    if not host_network_info.ipV6Enabled:
                        results['result'][host.name]['msg'] = "IPv6 is already disabled for host '%s'" % host.name
                    if host_network_info.ipV6Enabled:
                        changed = True
                        results['result'][host.name]['msg'] = ("IPv6 is already disabled for host '%s',"
                                                               " but a reboot is required!" % host.name)
                # Disable IPv6
                else:
                    if not self.module.check_mode:
                        try:
                            config = vim.host.NetworkConfig()
                            config.ipV6Enabled = False
                            host_network_system.UpdateNetworkConfig(config, "modify")
                            changed = True
                            results['result'][host.name]['changed'] = True
                            results['result'][host.name]['msg'] = "IPv6 disabled for host '%s'" % host.name
                        except (vim.fault.AlreadyExists, vim.fault.NotFound):
                            self.module.fail_json(msg="Network entity specified in the configuration for host '%s'"
                                                  " already exists" % host.name)
                        except vmodl.fault.InvalidArgument as invalid_argument:
                            self.module.fail_json(msg="Invalid parameter specified for host '%s' : %s" %
                                                  (host.name, to_native(invalid_argument.msg)))
                        except vim.fault.HostConfigFault as config_fault:
                            self.module.fail_json(msg="Failed to disable IPv6 for host '%s' due to : %s" %
                                                  (host.name, to_native(config_fault.msg)))
                        except vmodl.fault.NotSupported as not_supported:
                            self.module.fail_json(msg="Failed to disable IPv6 for host '%s' due to : %s" %
                                                  (host.name, to_native(not_supported.msg)))
                        except (vmodl.RuntimeFault, vmodl.MethodFault) as runtime_fault:
                            self.module.fail_json(msg="Failed to disable IPv6 for host '%s' due to : %s" %
                                                  (host.name, to_native(runtime_fault.msg)))
                    else:
                        changed = True
                        results['result'][host.name]['changed'] = True
                        results['result'][host.name]['msg'] = "IPv6 will be disabled for host '%s'" % host.name

            host_change_list.append(changed)

        if any(host_change_list):
            results['changed'] = True
        self.module.exit_json(**results)


def main():
    """
    Main
    """
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(default='enabled', choices=['enabled', 'disabled']),
        esxi_hostname=dict(type='str', required=False),
        cluster_name=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_one_of=[
                               ['cluster_name', 'esxi_hostname'],
                           ],
                           supports_check_mode=True
                           )

    ipv6 = VmwareHostIPv6(module)
    ipv6.ensure()


if __name__ == '__main__':
    main()
