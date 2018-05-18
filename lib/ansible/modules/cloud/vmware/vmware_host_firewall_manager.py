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
module: vmware_host_firewall_manager
short_description: Manage firewall configurations about an ESXi host
description:
- This module can be used to manage firewall configurations about an ESXi host when ESXi hostname or Cluster name is given.
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
    - Firewall settings are applied to every ESXi host system in given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
  esxi_hostname:
    description:
    - ESXi hostname.
    - Firewall settings are applied to this ESXi host system.
    - If C(cluster_name) is not given, this parameter is required.
  rules:
    description:
    - A list of Rule set which needs to be managed.
    - Each member of list is rule set name and state to be set the rule.
    - Both rule name and rule state are required parameters.
    - Please see examples for more information.
    default: []
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Enable vvold rule set for all ESXi Host in given Cluster
  vmware_host_firewall_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    cluster_name: cluster_name
    rules:
        - name: vvold
          enabled: True

- name: Enable vvold rule set for an ESXi Host
  vmware_host_firewall_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    rules:
        - name: vvold
          enabled: True

- name: Manage multiple rule set for an ESXi Host
  vmware_host_firewall_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    rules:
        - name: vvold
          enabled: True
        - name: CIMHttpServer
          enabled: False
'''

RETURN = r'''
rule_set_state:
    description:
    - dict with hostname as key and dict with firewall rule set facts as value
    returned: success
    type: dict
    sample: {
                "rule_set_state": {
                    "localhost.localdomain": {
                        "CIMHttpServer": {
                            "current_state": true,
                            "desired_state": true,
                            "previous_state": true
                        },
                        "vvold": {
                            "current_state": true,
                            "desired_state": true,
                            "previous_state": true
                        }
                    }
                }
            }
'''

try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native


class VmwareFirewallManager(PyVmomi):
    def __init__(self, module):
        super(VmwareFirewallManager, self).__init__(module)
        cluster_name = self.params.get('cluster_name', None)
        esxi_host_name = self.params.get('esxi_hostname', None)
        self.options = self.params.get('options', dict())
        self.hosts = self.get_all_host_objs(cluster_name=cluster_name, esxi_host_name=esxi_host_name)
        self.firewall_facts = dict()
        self.rule_options = self.module.params.get("rules")
        self.gather_rule_set()

    def gather_rule_set(self):
        for host in self.hosts:
            self.firewall_facts[host.name] = {}
            firewall_system = host.configManager.firewallSystem
            if firewall_system:
                for rule_set_obj in firewall_system.firewallInfo.ruleset:
                    temp_rule_dict = dict()
                    temp_rule_dict['enabled'] = rule_set_obj.enabled
                    self.firewall_facts[host.name][rule_set_obj.key] = temp_rule_dict

    def ensure(self):
        """
        Function to ensure rule set configuration

        """
        fw_change_list = []
        results = dict(changed=False, rule_set_state=dict())
        for host in self.hosts:
            firewall_system = host.configManager.firewallSystem
            if firewall_system is None:
                continue

            results['rule_set_state'][host.name] = dict()

            for rule_option in self.rule_options:
                rule_name = rule_option.get('name', None)
                if rule_name is None:
                    self.module.fail_json(msg="Please specify rule.name for rule set"
                                              " as it is required parameter.")
                if rule_name not in self.firewall_facts[host.name]:
                    self.module.fail_json(msg="rule named '%s' wasn't found." % rule_name)

                rule_enabled = rule_option.get('enabled', None)
                if rule_enabled is None:
                    self.module.fail_json(msg="Please specify rules.enabled for rule set"
                                              " %s as it is required parameter." % rule_name)

                current_rule_state = self.firewall_facts[host.name][rule_name]['enabled']
                if current_rule_state != rule_enabled:
                    try:
                        if rule_enabled:
                            firewall_system.EnableRuleset(id=rule_name)
                        else:
                            firewall_system.DisableRuleset(id=rule_name)
                        fw_change_list.append(True)
                    except vim.fault.NotFound as not_found:
                        self.module.fail_json(msg="Failed to enable rule set %s as"
                                                  " rule set id is unknown : %s" % (rule_name,
                                                                                    to_native(not_found.msg)))
                    except vim.fault.HostConfigFault as host_config_fault:
                        self.module.fail_json(msg="Failed to enabled rule set %s as an internal"
                                                  " error happened while reconfiguring"
                                                  " rule set : %s" % (rule_name,
                                                                      to_native(host_config_fault.msg)))
                results['rule_set_state'][host.name][rule_name] = dict(current_state=rule_enabled,
                                                                       previous_state=current_rule_state,
                                                                       desired_state=rule_enabled,
                                                                       )

        if any(fw_change_list):
            results['changed'] = True
        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        cluster_name=dict(type='str', required=False),
        esxi_hostname=dict(type='str', required=False),
        rules=dict(type='list', default=list(), required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_one_of=[
            ['cluster_name', 'esxi_hostname'],
        ]
    )

    vmware_firewall_manager = VmwareFirewallManager(module)
    vmware_firewall_manager.ensure()


if __name__ == "__main__":
    main()
