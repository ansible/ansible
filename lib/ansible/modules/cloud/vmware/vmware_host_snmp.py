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

DOCUMENTATION = '''
---
module: vmware_host_snmp
short_description: Configures SNMP on an ESXi host system
description:
- This module can be used to configure the embedded SNMP agent on an ESXi host.
version_added: 2.8
author:
- Christian Kotte (@ckotte)
notes:
- Tested on vSphere 6.5
- You need to reset the agent (to factory defaults) if you want to clear all community strings, trap targets, or filters
- SNMP v3 configuration isn't implemented yet
requirements:
- python >= 2.6
- PyVmomi
options:
  state:
    description:
        - Enable, disable, or reset the SNMP agent.
    type: str
    choices: [ disabled, enabled, reset ]
    default: disabled
  community:
    description:
        - List of SNMP community strings.
    type: list
  snmp_port:
    description:
        - Port used by the SNMP agent.
    type: int
    default: 161
  trap_targets:
    description:
        - A list of trap targets.
        - You need to use C(hostname), C(port), and C(community) for each trap target.
    default: []
  trap_filter:
    description:
        - A list of trap oids for traps not to be sent by agent,
          e.g. [ 1.3.6.1.4.1.6876.4.1.1.0, 1.3.6.1.4.1.6876.4.1.1.1 ]
        - Use value C(reset) to clear settings.
    type: list
  send_trap:
    description:
        - Send a test trap to validate the configuration.
    type: bool
    default: false
  hw_source:
    description:
        - Source hardware events from IPMI sensors or CIM Indications.
        - The embedded SNMP agent receives hardware events either from IPMI sensors C(sensors) or CIM indications C(indications).
    type: str
    choices: [ indications, sensors ]
    default: indications
  log_level:
    description:
        - Syslog logging level.
    type: str
    choices: [ debug, info, warning, error ]
    default: info
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Enable and configure SNMP community
  vmware_host_snmp:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    community: [ test ]
    state: enabled
    validate_certs: no
  delegate_to: localhost

- name: Configure SNMP traps and filters
  vmware_host_snmp:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    community: [ test ]
    trap_targets:
      - hostname: 192.168.1.100
        port: 162
        community: test123
      - hostname: 192.168.1.101
        port: 162
        community: test1234
    trap_filter:
      - 1.3.6.1.4.1.6876.4.1.1.0
      - 1.3.6.1.4.1.6876.4.1.1.1
    state: enabled
    validate_certs: no
  delegate_to: localhost

- name: Disable SNMP
  vmware_host_snmp:
    hostname: '{{ esxi_hostname }}'
    username: '{{ esxi_username }}'
    password: '{{ esxi_password }}'
    state: disabled
    validate_certs: no
  delegate_to: localhost
'''

RETURN = r'''
results:
    description: metadata about host system's SNMP configuration
    returned: always
    type: dict
    sample: {
        "esxi01": {
            "changed": false,
            "community": ["test"],
            "hw_source": "indications",
            "msg": "SNMP already configured properly",
            "port": 161,
            "state": "enabled",
            "trap_targets": []
        },
    }
'''

try:
    from pyVmomi import vim
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec, find_obj
from ansible.module_utils._text import to_native


class VmwareHostSnmp(PyVmomi):
    """Manage SNMP configuration for an ESXi host system"""

    def __init__(self, module):
        super(VmwareHostSnmp, self).__init__(module)

        if self.is_vcenter():
            self.module.fail_json(
                msg="You have to connect directly to the ESXi host. "
                "It's not possible to configure SNMP through a vCenter connection."
            )
        else:
            self.host = find_obj(self.content, [vim.HostSystem], None)
            if self.host is None:
                self.module.fail_json(msg="Failed to find host system.")

    def ensure(self):
        """Manage SNMP configuration for an ESXi host system"""
        results = dict(changed=False, result=dict())
        snmp_state = self.params.get('state')
        snmp_port = self.params.get('snmp_port')
        community = self.params.get('community')
        desired_trap_targets = self.params.get("trap_targets")
        hw_source = self.params.get("hw_source")
        log_level = self.params.get("log_level")
        send_trap = self.params.get("send_trap")
        trap_filter = self.params.get("trap_filter")
        event_filter = None
        if trap_filter:
            event_filter = ';'.join(trap_filter)
        changed = False
        reset_hint = None
        changed_list = []
        results = dict(msg='')

        snmp_system = self.host.configManager.snmpSystem
        if snmp_system:
            if snmp_system.configuration:
                snmp_config_spec = snmp_system.configuration
            else:
                self.module.fail_json(msg="SNMP agent configuration isn't supported on the ESXi host")
        else:
            self.module.fail_json(msg="SNMP system isn't available on the ESXi host")

        # Check state
        results['state'] = snmp_state
        if snmp_state == 'reset':
            changed = True
            # Get previous config
            if snmp_config_spec.enabled:
                results['state_previous'] = 'enabled'
            else:
                results['state_previous'] = 'disabled'
            results['port_previous'] = snmp_config_spec.port
            results['community_previous'] = snmp_config_spec.readOnlyCommunities
            results['trap_targets_previous'] = self.get_previous_targets(snmp_config_spec.trapTargets)
            for option in snmp_config_spec.option:
                if option.key == 'EnvEventSource' and option.value != hw_source:
                    results['hw_source_previous'] = option.value
                if option.key == 'loglevel' and option.value != hw_source:
                    results['log_level_previous'] = option.value
                if option.key == 'EventFilter' and option.value != hw_source:
                    results['trap_filter_previous'] = option.value.split(';')
            # Build factory default config
            destination = vim.host.SnmpSystem.SnmpConfigSpec.Destination()
            destination.hostName = ""
            destination.port = 0
            destination.community = ""
            options = []
            options.append(self.create_option('EnvEventSource', 'indications'))
            options.append(self.create_option('EventFilter', 'reset'))
            snmp_config_spec = vim.host.SnmpSystem.SnmpConfigSpec()
            # Looks like this value is causing the reset
            snmp_config_spec.readOnlyCommunities = [""]
            snmp_config_spec.trapTargets = [destination]
            snmp_config_spec.port = 161
            snmp_config_spec.enabled = False
            snmp_config_spec.option = options
        else:
            if snmp_state == 'enabled' and not snmp_config_spec.enabled:
                changed = True
                changed_list.append("state")
                results['state_previous'] = 'disabled'
                snmp_config_spec.enabled = True
            elif snmp_state == 'disabled' and snmp_config_spec.enabled:
                changed = True
                changed_list.append("state")
                results['state_previous'] = 'enabled'
                snmp_config_spec.enabled = False

            # Check port
            results['port'] = snmp_port
            if snmp_config_spec.port != snmp_port:
                changed = True
                changed_list.append("port")
                results['port_previous'] = snmp_config_spec.port
                snmp_config_spec.port = snmp_port

            # Check read-only community strings
            results['community'] = community
            if snmp_config_spec.readOnlyCommunities != community:
                changed = True
                changed_list.append("community list")
                results['community_previous'] = snmp_config_spec.readOnlyCommunities
                if community:
                    snmp_config_spec.readOnlyCommunities = community
                else:
                    # Doesn't work. Need to reset config instead
                    # snmp_config_spec.readOnlyCommunities = []
                    reset_hint = True

            # Check trap targets
            results['trap_targets'] = desired_trap_targets
            if snmp_config_spec.trapTargets:
                if desired_trap_targets:
                    temp_desired_targets = []
                    # Loop through desired targets
                    for target in desired_trap_targets:
                        dest_hostname, dest_port, dest_community = self.check_if_options_are_valid(target)
                        trap_target_found = False
                        for trap_target in snmp_config_spec.trapTargets:
                            if trap_target.hostName == dest_hostname:
                                if trap_target.port != dest_port or trap_target.community != dest_community:
                                    changed = True
                                    changed_list.append("trap target '%s'" % dest_hostname)
                                trap_target_found = True
                                break
                        if not trap_target_found:
                            changed = True
                            changed_list.append("trap target '%s'" % dest_hostname)
                        # Build destination and add to temp target list
                        destination = self.build_destination(dest_hostname, dest_port, dest_community)
                        temp_desired_targets.append(destination)
                    # Loop through existing targets to find targets that need to be deleted
                    for trap_target in snmp_config_spec.trapTargets:
                        target_found = False
                        for target in desired_trap_targets:
                            if trap_target.hostName == target.get('hostname'):
                                target_found = True
                                break
                        if not target_found:
                            changed = True
                            changed_list.append("trap target '%s'" % trap_target.hostName)
                    # Configure trap targets if something has changed
                    if changed:
                        results['trap_targets_previous'] = self.get_previous_targets(snmp_config_spec.trapTargets)
                        snmp_config_spec.trapTargets = temp_desired_targets
                else:
                    changed = True
                    changed_list.append("trap targets")
                    results['trap_targets_previous'] = self.get_previous_targets(snmp_config_spec.trapTargets)
                    # Doesn't work. Need to reset config instead
                    # snmp_config_spec.trapTargets = []
                    reset_hint = True
            else:
                if desired_trap_targets:
                    changed = True
                    changed_list.append("trap targets")
                    results['trap_targets_previous'] = None
                    desired_targets = []
                    for target in desired_trap_targets:
                        dest_hostname, dest_port, dest_community = self.check_if_options_are_valid(target)
                        destination = self.build_destination(dest_hostname, dest_port, dest_community)
                        desired_targets.append(destination)
                    snmp_config_spec.trapTargets = desired_targets

            # Check options
            results['hw_source'] = hw_source
            results['log_level'] = log_level
            results['trap_filter'] = trap_filter
            event_filter_found = False
            if snmp_config_spec.option:
                for option in snmp_config_spec.option:
                    if option.key == 'EnvEventSource' and option.value != hw_source:
                        changed = True
                        changed_list.append("HW source")
                        results['hw_source_previous'] = option.value
                        option.value = hw_source
                    if option.key == 'loglevel' and option.value != log_level:
                        changed = True
                        changed_list.append("log level")
                        results['log_level_previous'] = option.value
                        option.value = log_level
                    if option.key == 'EventFilter':
                        event_filter_found = True
                        if event_filter and option.value != event_filter:
                            changed = True
                            changed_list.append("trap filter")
                            results['trap_filter_previous'] = option.value.split(';')
                            option.value = event_filter
            if trap_filter and not event_filter_found:
                changed = True
                changed_list.append("trap filter")
                results['trap_filter_previous'] = []
                snmp_config_spec.option.append(self.create_option('EventFilter', event_filter))
            elif not trap_filter and event_filter_found:
                changed = True
                changed_list.append("trap filter")
                # options = []
                for option in snmp_config_spec.option:
                    if option.key == 'EventFilter':
                        results['trap_filter_previous'] = option.value.split(';')
                    # else:
                    #     options.append(option)
                # Doesn't work. Need to reset config instead
                # snmp_config_spec.option = options
                reset_hint = True

        if changed:
            if snmp_state == 'reset':
                if self.module.check_mode:
                    message = "SNMP agent would be reset to factory defaults"
                else:
                    message = "SNMP agent config reset to factory defaults"
            else:
                if self.module.check_mode:
                    changed_suffix = ' would be changed'
                else:
                    changed_suffix = ' changed'
                if len(changed_list) > 2:
                    message = ', '.join(changed_list[:-1]) + ', and ' + str(changed_list[-1])
                elif len(changed_list) == 2:
                    message = ' and '.join(changed_list)
                elif len(changed_list) == 1:
                    message = changed_list[0]
                message = "SNMP " + message + changed_suffix
            if reset_hint:
                message += ". Agent reset required!"
            if not self.module.check_mode:
                try:
                    snmp_system.ReconfigureSnmpAgent(snmp_config_spec)
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(
                        msg="Not found : %s" % to_native(not_found)
                    )
                except vim.fault.InsufficientResourcesFault as insufficient_resources:
                    self.module.fail_json(
                        msg="Insufficient resources : %s" % to_native(insufficient_resources)
                    )
        else:
            message = "SNMP already configured properly"
        if not snmp_state == 'reset' and send_trap and desired_trap_targets:
            # Check if there was a change before
            if changed:
                message += " and "
            else:
                message += ", but "
            changed = True
            if self.module.check_mode:
                message = message + "a test trap would be sent"
            else:
                try:
                    snmp_system.SendTestNotification()
                    message = message + "a test trap was sent"
                except vim.fault.NotFound as not_found:
                    self.module.fail_json(
                        msg="Error during trap test : Not found : %s" % to_native(not_found)
                    )
                except vim.fault.InsufficientResourcesFault as insufficient_resources:
                    self.module.fail_json(
                        msg="Error during trap test : Insufficient resources : %s" % to_native(insufficient_resources)
                    )
        results['changed'] = changed
        results['msg'] = message

        self.module.exit_json(**results)

    @staticmethod
    def create_option(key, value):
        """Create option"""
        option = vim.KeyValue()
        option.key = key
        option.value = value
        return option

    @staticmethod
    def get_previous_targets(trap_targets):
        """Get target entries from trap targets object"""
        previous_targets = []
        for target in trap_targets:
            temp = dict()
            temp['hostname'] = target.hostName
            temp['port'] = target.port
            temp['community'] = target.community
            previous_targets.append(temp)
        return previous_targets

    @staticmethod
    def build_destination(dest_hostname, dest_port, dest_community):
        """Build destination spec"""
        destination = vim.host.SnmpSystem.SnmpConfigSpec.Destination()
        destination.hostName = dest_hostname
        destination.port = dest_port
        destination.community = dest_community
        return destination

    def check_if_options_are_valid(self, target):
        """Check if options are valid"""
        dest_hostname = target.get('hostname', None)
        if dest_hostname is None:
            self.module.fail_json(
                msg="Please specify hostname for the trap target as it's a required parameter"
            )
        dest_port = target.get('port', None)
        if dest_port is None:
            self.module.fail_json(
                msg="Please specify port for the trap target as it's a required parameter"
            )
        dest_community = target.get('community', None)
        if dest_community is None:
            self.module.fail_json(
                msg="Please specify community for the trap target as it's a required parameter"
            )
        return dest_hostname, dest_port, dest_community


def main():
    """Main"""
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        state=dict(type='str', default='disabled', choices=['enabled', 'disabled', 'reset']),
        snmp_port=dict(type='int', default=161),
        community=dict(type='list', default=[]),
        trap_targets=dict(type='list', default=list()),
        trap_filter=dict(type='list'),
        hw_source=dict(type='str', default='indications', choices=['indications', 'sensors']),
        log_level=dict(type='str', default='info', choices=['debug', 'info', 'warning', 'error']),
        send_trap=dict(type='bool', default=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    host_snmp = VmwareHostSnmp(module)
    host_snmp.ensure()


if __name__ == '__main__':
    main()
