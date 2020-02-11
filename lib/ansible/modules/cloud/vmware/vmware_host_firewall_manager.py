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
- Aaron Longchamps (@alongchamps)
notes:
- Tested on vSphere 6.0, vSphere 6.5
requirements:
- python >= 2.6
- PyVmomi
options:
  cluster_name:
    description:
    - Name of the cluster.
    - Firewall settings are applied to every ESXi host system in given cluster.
    - If C(esxi_hostname) is not given, this parameter is required.
    type: str
  esxi_hostname:
    description:
    - ESXi hostname.
    - Firewall settings are applied to this ESXi host system.
    - If C(cluster_name) is not given, this parameter is required.
    type: str
  rules:
    description:
    - A list of Rule set which needs to be managed.
    - Each member of list is rule set name and state to be set the rule.
    - Both rule name and rule state are required parameters.
    - Additional IPs and networks can also be specified
    - Please see examples for more information.
    default: []
    type: list
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
  delegate_to: localhost

- name: Enable vvold rule set for an ESXi Host
  vmware_host_firewall_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    rules:
        - name: vvold
          enabled: True
  delegate_to: localhost

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
  delegate_to: localhost

- name: Manage IP and network based firewall permissions for ESXi
  vmware_host_firewall_manager:
    hostname: '{{ vcenter_hostname }}'
    username: '{{ vcenter_username }}'
    password: '{{ vcenter_password }}'
    esxi_hostname: '{{ esxi_hostname }}'
    rules:
        - name: gdbserver
          enabled: True
          allowed_hosts:
            all_ip: False
            ip_address:
              - 192.168.20.10
              - 192.168.20.11
        - name: CIMHttpServer
          enabled: True
          allowed_hosts:
            all_ip: False
            ip_network:
              - 192.168.100.0/24
        - name: remoteSerialPort
          enabled: True
          allowed_hosts:
            all_ip: False
            ip_address:
              - 192.168.100.11
            ip_network:
              - 192.168.200.0/24
  delegate_to: localhost
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
                            "current_state": False,
                            "desired_state": False,
                            "previous_state": True,
                            "allowed_hosts": {
                                "current_allowed_all": True,
                                "previous_allowed_all": True,
                                "desired_allowed_all": True,
                                "current_allowed_ip": [],
                                "previous_allowed_ip": [],
                                "desired_allowed_ip": [],
                                "current_allowed_networks": [],
                                "previous_allowed_networks": [],
                                "desired_allowed_networks": [],
                            }
                        },
                        "remoteSerialPort": {
                            "current_state": True,
                            "desired_state": True,
                            "previous_state": True,
                            "allowed_hosts": {
                                "current_allowed_all": False,
                                "previous_allowed_all": True,
                                "desired_allowed_all": False,
                                "current_allowed_ip": ["192.168.100.11"],
                                "previous_allowed_ip": [],
                                "desired_allowed_ip": ["192.168.100.11"],
                                "current_allowed_networks": ["192.168.200.0/24"],
                                "previous_allowed_networks": [],
                                "desired_allowed_networks": ["192.168.200.0/24"],
                            }
                        }
                    }
                }
            }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import vmware_argument_spec, PyVmomi
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.compat import ipaddress


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
                    allowed_host = rule_set_obj.allowedHosts
                    rule_allow_host = dict()
                    rule_allow_host['ip_address'] = allowed_host.ipAddress
                    rule_allow_host['ip_network'] = [ip.network + "/" + str(ip.prefixLength) for ip in allowed_host.ipNetwork]
                    rule_allow_host['all_ip'] = allowed_host.allIp
                    temp_rule_dict['allowed_hosts'] = rule_allow_host
                    self.firewall_facts[host.name][rule_set_obj.key] = temp_rule_dict

    def check_params(self):
        rules_by_host = {}
        for host in self.hosts:
            rules_by_host[host.name] = self.firewall_facts[host.name].keys()

        for rule_option in self.rule_options:
            rule_name = rule_option.get('name')
            if rule_name is None:
                self.module.fail_json(msg="Please specify rule.name for rule set"
                                          " as it is required parameter.")
            hosts_with_rule_name = [h for h, r in rules_by_host.items() if rule_name in r]
            hosts_without_rule_name = set([i.name for i in self.hosts]) - set(hosts_with_rule_name)
            if hosts_without_rule_name:
                self.module.fail_json(msg="rule named '%s' wasn't found on hosts: %s" % (
                    rule_name, hosts_without_rule_name))

            if 'enabled' not in rule_option:
                self.module.fail_json(msg="Please specify rules.enabled for rule set"
                                          " %s as it is required parameter." % rule_name)

            allowed_hosts = rule_option.get('allowed_hosts', {})
            ip_addresses = allowed_hosts.get('ip_address', [])
            ip_networks = allowed_hosts.get('ip_network', [])
            for ip_address in ip_addresses:
                try:
                    ipaddress.ip_address(to_text(ip_address))
                except ValueError:
                    self.module.fail_json(msg="The provided IP address %s is not a valid IP"
                                              " for the rule %s" % (ip_address, rule_name))

            for ip_network in ip_networks:
                try:
                    ipaddress.ip_network(ip_network)
                except ValueError:
                    self.module.fail_json(msg="The provided IP network %s is not a valid network"
                                              " for the rule %s" % (ip_network, rule_name))

    def ensure(self):
        """
        Function to ensure rule set configuration

        """
        fw_change_list = []
        enable_disable_changed = False
        allowed_ip_changed = False
        results = dict(changed=False, rule_set_state=dict())
        for host in self.hosts:
            firewall_system = host.configManager.firewallSystem
            if firewall_system is None:
                continue
            results['rule_set_state'][host.name] = {}
            for rule_option in self.rule_options:
                rule_name = rule_option.get('name', None)

                current_rule_state = self.firewall_facts[host.name][rule_name]['enabled']
                if current_rule_state != rule_option['enabled']:
                    try:
                        if not self.module.check_mode:
                            if rule_option['enabled']:
                                firewall_system.EnableRuleset(id=rule_name)
                            else:
                                firewall_system.DisableRuleset(id=rule_name)
                        # keep track of changes as we go
                        enable_disable_changed = True
                    except vim.fault.NotFound as not_found:
                        self.module.fail_json(msg="Failed to enable rule set %s as"
                                                  " rule set id is unknown : %s" % (
                                                      rule_name,
                                                      to_native(not_found.msg)))
                    except vim.fault.HostConfigFault as host_config_fault:
                        self.module.fail_json(msg="Failed to enabled rule set %s as an internal"
                                                  " error happened while reconfiguring"
                                                  " rule set : %s" % (
                                                      rule_name,
                                                      to_native(host_config_fault.msg)))

                # save variables here for comparison later and change tracking
                # also covers cases where inputs may be null
                permitted_networking = self.firewall_facts[host.name][rule_name]
                rule_allows_all = permitted_networking['allowed_hosts']['all_ip']
                rule_allowed_ips = set(permitted_networking['allowed_hosts']['ip_address'])
                rule_allowed_networks = set(permitted_networking['allowed_hosts']['ip_network'])

                allowed_hosts = rule_option.get('allowed_hosts', {})
                playbook_allows_all = allowed_hosts.get('all_ip', False)
                playbook_allowed_ips = set(allowed_hosts.get('ip_address', []))
                playbook_allowed_networks = set(allowed_hosts.get('ip_network', []))

                # compare what is configured on the firewall rule with what the playbook provides
                allowed_all_ips_different = bool(rule_allows_all != playbook_allows_all)
                ip_list_different = bool(rule_allowed_ips != playbook_allowed_ips)
                ip_network_different = bool(rule_allowed_networks != playbook_allowed_networks)

                # apply everything here in one function call
                if allowed_all_ips_different is True or ip_list_different is True or ip_network_different is True:
                    try:
                        allowed_ip_changed = True
                        if not self.module.check_mode:
                            # setup spec
                            firewall_spec = vim.host.Ruleset.RulesetSpec()
                            firewall_spec.allowedHosts = vim.host.Ruleset.IpList()
                            firewall_spec.allowedHosts.allIp = playbook_allows_all
                            firewall_spec.allowedHosts.ipAddress = list(playbook_allowed_ips)
                            firewall_spec.allowedHosts.ipNetwork = []

                            for i in playbook_allowed_networks:
                                address, mask = i.split('/')
                                tmp_ip_network_spec = vim.host.Ruleset.IpNetwork()
                                tmp_ip_network_spec.network = address
                                tmp_ip_network_spec.prefixLength = int(mask)
                                firewall_spec.allowedHosts.ipNetwork.append(tmp_ip_network_spec)

                            firewall_system.UpdateRuleset(id=rule_name, spec=firewall_spec)
                    except vim.fault.NotFound as not_found:
                        self.module.fail_json(msg="Failed to configure rule set %s as"
                                                  " rule set id is unknown : %s" % (rule_name,
                                                                                    to_native(not_found.msg)))
                    except vim.fault.HostConfigFault as host_config_fault:
                        self.module.fail_json(msg="Failed to configure rule set %s as an internal"
                                                  " error happened while reconfiguring"
                                                  " rule set : %s" % (rule_name,
                                                                      to_native(host_config_fault.msg)))
                    except vim.fault.RuntimeFault as runtime_fault:
                        self.module.fail_json(msg="Failed to configure the rule set %s as a runtime"
                                                  " error happened while applying the reconfiguration:"
                                                  " %s" % (rule_name, to_native(runtime_fault.msg)))

                results['rule_set_state'][host.name][rule_name] = {
                    'current_state': rule_option['enabled'],
                    'previous_state': current_rule_state,
                    'desired_state': rule_option['enabled'],
                    'allowed_hosts': {
                        'current_allowed_all': playbook_allows_all,
                        'previous_allowed_all': permitted_networking['allowed_hosts']['all_ip'],
                        'desired_allowed_all': playbook_allows_all,
                        'current_allowed_ip': playbook_allowed_ips,
                        'previous_allowed_ip': set(permitted_networking['allowed_hosts']['ip_address']),
                        'desired_allowed_ip': playbook_allowed_ips,
                        'current_allowed_networks': playbook_allowed_networks,
                        'previous_allowed_networks': set(permitted_networking['allowed_hosts']['ip_network']),
                        'desired_allowed_networks': playbook_allowed_networks,
                    }
                }

        if enable_disable_changed or allowed_ip_changed:
            fw_change_list.append(True)

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
        ],
        supports_check_mode=True
    )

    for rule_option in module.params.get("rules", []):
        if 'allowed_hosts' in rule_option:
            if isinstance(rule_option['allowed_hosts'], list):
                if len(rule_option['allowed_hosts']) == 1:
                    allowed_hosts = rule_option['allowed_hosts'][0]
                    rule_option['allowed_hosts'] = allowed_hosts
                    module.deprecate('allowed_hosts should be a dict, not a list', '2.13')

    vmware_firewall_manager = VmwareFirewallManager(module)
    vmware_firewall_manager.check_params()
    vmware_firewall_manager.ensure()


if __name__ == "__main__":
    main()
