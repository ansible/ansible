#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Abhijeet Kasurde <akasurde@redhat.com>
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
module: vmware_guest_customization
short_description: Manage virtual machine customization specifications
description:
    - This module can be used to create, delete, update and rename virtual machine's customization specifications.
version_added: 2.9
author:
- Abhijeet Kasurde (@Akasurde)
notes:
    - Tested on ESXi 6.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
    spec_name:
      description:
      - Unique name identifying the customization specification.
      - This parameter is case sensitive.
      - This name can be used as C(customization_spec) is M(vmware_guest) module for customizing operating systems.
      required: True
      type: str
    spec_type:
      description:
      - Type of network identity and settings.
      - If set to C(Linux), then LinuxPrep is used for the customization. Used for Linux like operating systems.
      - If set to C(Windows), then SysPrep is used for the customization. Used for Windows like operating systems.
      - If not set, then C(Linux) is used as default.
      default: 'Linux'
      choices: ['Linux', 'Windows']
      type: str
    spec_description:
      description:
      - The description for the given customization specification.
      type: str
    networks:
      description:
      - A list of networks.
      - This is a required parameter, if C(state) is set to C(present).
      - All parameters and VMware object names are case sensitive.
      - 'One of the below parameters is required per entry:'
      - ' - C(type) (string): Type of IP address assignment (either C(dhcp) or C(static)). C(dhcp) is default.'
      - ' - C(ip) (string): Static IP address and implies C(type) as C(static).'
      - ' - C(netmask) (string): Static netmask required for C(ip) and implies C(type) as C(static).'
      - ' - C(gateway) (string): Static gateway.'
      - ' - C(dns_servers) (string): DNS servers for this network interface (Windows).'
      - ' - C(domain) (string): Domain name for this network interface (Windows).'
      type: list
    dns_servers:
      description:
      - A list of DNS servers.
      - This parameter applies to both Linux and Windows customization.
      type: list
    dns_suffix:
      description:
      - 'A list of domain suffixes, also known as DNS search path (default: C(domain) parameter).'
      - This parameter applies to both Linux and Windows customization.
      type: list
    domain:
      description:
      - DNS domain name to use.
      - This parameter applies to both Linux and Windows customization.
      type: str
    vm_hostname:
      description:
      - Short Full Qualified Domain Name.
      - This parameter applies to both Linux and Windows customization.
      - Do not provide domain name with this parameter.
      - 'Allowed characters are alphanumeric (uppercase and lowercase) and minus, rest of the characters are dropped as per RFC 952.'
      - This parameter is required if C(state) is set to C(present).
      type: str
    fullname:
      description:
      - Server owner name.
      - This parameter applies to Windows customization.
      default: 'Administrator'
      type: str
    orgname:
      description:
      - Organization name.
      - This parameter applies to Windows customization.
      default: ACME
      type: str
    productid:
      description:
      - Windows Product ID.
      - This parameter applies to Windows customization.
      type: str
    autologon:
      description:
      - Auto logon after Windows VM customization.
      - This parameter applies to Windows customization.
      default: False
      type: bool
    autologoncount:
      description:
      - Number of autologon after reboot.
      - This parameter applies to Windows customization.
      - This parameter is applied, only if C(autologon) is set.
      default: 1
      type: int
    timezone:
      description:
      - Timezone (See U(https://msdn.microsoft.com/en-us/library/ms912391.aspx)).
      - This parameter applies to Windows customization.
      type: str
    windows_password:
      description:
      - Local administrator password.
      - This parameter applies to Windows customization.
      type: str
    domainadmin:
      description:
      - User used to join in AD domain.
      - This parameter is required if C(joindomain) is set.
      - This parameter applies to Windows customization.
      type: str
    domainadminpassword:
      description:
      - Password used to join in AD domain.
      - This parameter is required if C(joindomain) is set.
      - This parameter applies to Windows customization.
      type: str
    joindomain:
      description:
      - AD domain to join.
      - This parameter is not compatible with C(joinworkgroup).
      - If set, then C(domainadmin) and C(domainadminpassword) are required parameters.
      - This parameter applies to Windows customization.
      type: str
    joinworkgroup:
      description:
      - Workgroup to join.
      - This parameter is not compatible with C(joindomain).
      - This parameter applies to Windows customization.
      default: 'WORKGROUP'
      type: str
    runonce:
      description:
      - A list of commands to run at first user logon.
      - This parameter applies to Windows customization.
      type: list
    new_spec_name:
      description:
      - New spec name to change existing spec name to.
      - If C(state) is set to C(present) and customization specification with given name is present with this parameter,
        then specification is renamed to this value.
      type: str
    state:
      description:
      - Indicate desired state of the customization specification.
      - If set to C(present) and customization specification with given name is absent, then customization specification is created.
      - If set to C(present) and customization specification with given name is present, then customization specification is updated.
      - If set to C(absent) and customization specification with given name is present, then customization specification is deleted.
      - If set to C(absent) and customization specification with given name is absent, then no action is taken.
      choices: ['present', 'absent']
      default: present
      type: str
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = r'''
- name: Create a Linux Customization specification
  vmware_guest_customization:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    validate_certs: False
    state: present
    spec_name: "{{ spec_name }}"
    spec_description: 'sample Linux spec description'
    spec_type: 'Linux'
    vm_hostname: sample1
    networks:
      - type: 'static'
        ip: '192.168.10.10'
        netmask: '255.255.255.0'
  delegate_to: localhost

- name: Create a Windows Customization specification
  vmware_guest_customization:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    validate_certs: False
    state: present
    spec_name: "{{ spec_name_win }}"
    spec_description: 'Windows Spec description'
    spec_type: 'Windows'
    vm_hostname: sample_win1
    networks:
      - type: 'dhcp'
    autologon: yes
    dns_servers:
      - 192.168.10.1
      - 192.168.10.2
    domain: lab.example.com
    windows_password: new_vm_password
    runonce:
      - powershell.exe -ExecutionPolicy Unrestricted -File C:\Windows\Temp\ConfigureRemotingForAnsible.ps1 -ForceNewSSLCert -EnableCredSSP
  delegate_to: localhost

- name: rename customization specification
  vmware_guest_customization:
    hostname: "{{ vcenter_server }}"
    username: "{{ vcenter_user }}"
    password: "{{ vcenter_pass }}"
    validate_certs: False
    state: present
    spec_name: "{{ spec_name }}"
    new_spec_name: "{{ new_spec_name }}"
  delegate_to: localhost
'''

RETURN = r''' # '''

import re
try:
    from pyVmomi import vim, vmodl
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.vmware import PyVmomi, vmware_argument_spec
from ansible.module_utils._text import to_native


class VmwareCustomizationMgr(PyVmomi):
    def __init__(self, module):
        super(VmwareCustomizationMgr, self).__init__(module)

        self.cc_mgr = self.content.customizationSpecManager
        if self.cc_mgr is None:
            self.module.fail_json(msg="Failed to get customization spec manager.")

        self.state = self.params.get('state')
        self.spec_name = self.params.get('spec_name')

    def process_state(self):
        spec_states = {
            'absent': {
                'present': self.state_remove_custom_spec,
                'absent': self.state_exit_unchanged,
            },
            'present': {
                'present': self.state_update_custom_spec,
                'absent': self.state_create_custom_spec,
            }
        }
        try:
            spec_states[self.state][self.check_custom_spec_state()]()
        except vmodl.RuntimeFault as runtime_fault:
            self.module.fail_json(msg=to_native(runtime_fault.msg))
        except vmodl.MethodFault as method_fault:
            self.module.fail_json(msg=to_native(method_fault.msg))
        except Exception as e:
            self.module.fail_json(msg=to_native(e))

    def check_custom_spec_state(self):
        return 'present' if self.cc_mgr.DoesCustomizationSpecExist(name=self.spec_name) else 'absent'

    def state_exit_unchanged(self):
        self.module.exit_json(changed=False)

    def state_remove_custom_spec(self):
        if self.module.check_mode:
            changed = True
        else:
            self.cc_mgr.DeleteCustomizationSpec(name=self.spec_name)
            changed = True if self.check_custom_spec_state() == 'absent' else False

        self.module.exit_json(changed=changed)

    def state_update_custom_spec(self):
        changed = False
        current_spec = None
        try:
            current_spec = self.cc_mgr.GetCustomizationSpec(name=self.spec_name)
        except vim.fault.NotFound as e:
            self.module.fail_json(msg="Failed to retrieve customization"
                                      " specification '%s' while updating : %s" % (self.spec_name,
                                                                                   to_native(e.msg)))
        spec_type = self.params.get('spec_type')
        if spec_type != current_spec.info.type:
            self.module.fail_json(msg="Can not change the type of customization"
                                      " specification from '%s' to '%s'" % (spec_type,
                                                                            current_spec.info.type))

        new_spec_name = self.params.get('new_spec_name')
        if new_spec_name and new_spec_name != current_spec.info.name:
            if self.cc_mgr.DoesCustomizationSpecExist(name=new_spec_name):
                self.module.fail_json(msg="Unable to rename customization specification. Please specify"
                                          " different name for customization spec as '%s' already exists"
                                          " in the given configuration." % new_spec_name)
            if not self.module.check_mode:
                self.cc_mgr.RenameCustomizationSpec(name=self.spec_name, newName=new_spec_name)
            self.module.exit_json(changed=True)

        reconf_flag = False
        new_description = self.params.get('spec_description')
        if new_description and current_spec.info.description != new_description:
            current_spec.info.description = new_description
            reconf_flag = True

        new_hostname = self.params.get('vm_hostname')
        if new_hostname and current_spec.spec.identity.hostName.name != new_hostname:
            current_spec.spec.identity.hostName.name = new_hostname
            reconf_flag = True

        new_domain = self.params.get('domain', None)
        if new_domain and current_spec.spec.identity.doamin != new_domain:
            current_spec.spec.identity.domain = new_domain
            reconf_flag = True

        new_timezone = self.params.get('timezone')
        if new_timezone and current_spec.spec.identity.timeZone != new_timezone:
            current_spec.spec.identity.timeZone = new_timezone
            reconf_flag = True

        new_dns_servers = self.params.get('dns_servers')
        if new_dns_servers and set(current_spec.globalIPSettings.dnsServerList) != set(new_dns_servers):
            current_spec.globalIPSettings.dnsServerList = new_dns_servers
            reconf_flag = True

        new_dns_suffix = self.params.get('dns_suffix')
        if new_dns_servers and set(current_spec.globalIPSettings.dnsSuffixList) != set(new_dns_suffix):
            current_spec.globalIPSettings.dnsSuffixList = new_dns_suffix
            reconf_flag = True

        if reconf_flag:
            try:
                if not self.module.check_mode:
                    self.cc_mgr.OverwriteCustomizationSpec(item=current_spec)
                changed = True
            except vim.fault.NotFound as not_found:
                self.module.fail_json(msg="Failed to find '%s' to overwrite : %s" % (self.spec_name,
                                                                                     to_native(not_found.msg)))
            except vim.fault.CustomizationFault as fault:
                self.module.fail_json(msg="Failed to overwrite '%s' due to %s" % (self.spec_name,
                                                                                  to_native(fault.msg)))
            except vim.fault.ConcurrentAccess as concurrent_exc:
                self.module.fail_json(msg="Failed to overwrite '%s' as another application"
                                          " is also accessing the customization spec %s" % (self.spec_name,
                                                                                            to_native(concurrent_exc.msg)))

            except Exception as generic_exc:
                self.module.fail_json(msg="Failed to overwrite '%s' due to generic"
                                          " exception %s" % (self.spec_name, to_native(generic_exc)))

        self.module.exit_json(changed=changed)

    def state_create_custom_spec(self):
        results = dict(changed=False)
        spec_type = self.params.get('spec_type')
        networks = self.params.get('networks', [])
        if networks is None:
            self.module.fail_json(msg="networks parameter can not be None.")

        # Create customization item and add name and type
        custom_item = vim.CustomizationSpecItem()
        custom_spec_info = vim.CustomizationSpecInfo()
        custom_spec_info.name = self.spec_name
        custom_spec_info.description = self.params.get('spec_description')
        custom_spec_info.type = spec_type
        custom_item.info = custom_spec_info

        # Create a specification
        custom_spec = vim.vm.customization.Specification()

        nic_setting_map = []
        for network in networks:
            # Adapter Mapping
            ip_adapter_mapping = vim.vm.customization.AdapterMapping()
            ip_adapter_mapping.adapter = vim.vm.customization.IPSettings()

            if 'type' in network:
                if network['type'] not in ['static', 'dhcp']:
                    network['type'] = 'dhcp'

                if network['type'] == 'static' and ('ip' not in network or 'netmask' not in network):
                    self.module.fail_json(msg="network type is set to 'static' but no 'ip' or 'netmask' set.")
            else:
                # User wants default DHCP option
                network['type'] = 'dhcp'

            if network['type'] == 'static' and 'ip' in network and 'netmask' in network:
                ip_adapter_mapping.adapter.ip = vim.vm.customization.FixedIp()
                ip_adapter_mapping.adapter.ip.ipAddress = str(network['ip'])
                ip_adapter_mapping.adapter.subnetMask = str(network['netmask'])
            elif network['type'] == 'dhcp':
                ip_adapter_mapping.adapter.ip = vim.vm.customization.DhcpIpGenerator()

            if 'gateway' in network:
                ip_adapter_mapping.adapter.gateway = network['gateway']

            if 'domain' in network:
                ip_adapter_mapping.adapter.dnsDomain = network['domain']

            nic_setting_map.append(ip_adapter_mapping)

        custom_spec.nicSettingMap = nic_setting_map

        # Global DNS settings
        global_ip = vim.vm.customization.GlobalIPSettings()
        if 'dns_servers' in self.params:
            global_ip.dnsServerList = self.params['dns_servers']

        if 'dns_suffix' in self.params:
            global_ip.dnsSuffixList = self.params['dns_suffix']
        elif 'domain' in self.params:
            global_ip.dnsSuffixList = self.params['domain']

        custom_spec.globalIPSettings = global_ip

        if spec_type == 'Windows':
            custom_spec.identity = vim.vm.customization.Sysprep()
            custom_spec.identity.userData = vim.vm.customization.UserData()

            # Setting hostName, orgName and fullName is mandatory, so we set some default when missing
            custom_spec.identity.userData.computerName = vim.vm.customization.FixedName()
            computer_name = str(self.params.get('vm_hostname', None))
            if computer_name is None:
                self.module.fail_json(msg="vm_hostname can not be None.")
            custom_spec.identity.userData.computerName.name = computer_name
            custom_spec.identity.userData.fullName = str(self.params.get('fullname', 'Administrator'))
            custom_spec.identity.userData.orgName = str(self.params.get('orgname', 'ACME'))

            if 'productid' in self.params:
                custom_spec.identity.userData.productId = str(self.params['productid'])

            custom_spec.identity.guiUnattended = vim.vm.customization.GuiUnattended()

            if 'autologon' in self.params:
                custom_spec.identity.guiUnattended.autoLogon = self.params['autologon']
                custom_spec.identity.guiUnattended.autoLogonCount = self.params.get('autologoncount', 1)

            if 'timezone' in self.params:
                custom_spec.identity.guiUnattended.timeZone = self.params['timezone']

            custom_spec.identity.identification = vim.vm.customization.Identification()

            if self.params.get('windows_password', '') != '':
                custom_spec.identity.guiUnattended.password = vim.vm.customization.Password()
                custom_spec.identity.guiUnattended.password.value = str(self.params['windows_password'])
                custom_spec.identity.guiUnattended.password.plainText = True

            if 'joindomain' in self.params:
                if 'domainadmin' not in self.params or 'domainadminpassword' not in self.params:
                    self.module.fail_json(msg="'domainadmin' and 'domainadminpassword' entries are mandatory when"
                                              " 'joindomain' feature used.")

                custom_spec.identity.identification.domainAdmin = str(self.params['domainadmin'])
                custom_spec.identity.identification.joinDomain = str(self.params['joindomain'])
                custom_spec.identity.identification.domainAdminPassword = vim.vm.customization.Password()
                custom_spec.identity.identification.domainAdminPassword.value = str(self.params['domainadminpassword'])
                custom_spec.identity.identification.domainAdminPassword.plainText = True

            elif 'joinworkgroup' in self.params:
                custom_spec.identity.identification.joinWorkgroup = str(self.params['joinworkgroup'])

            if 'runonce' in self.params:
                custom_spec.identity.guiRunOnce = vim.vm.customization.GuiRunOnce()
                custom_spec.identity.guiRunOnce.commandList = self.params['runonce']
        elif spec_type == 'Linux':
            # For Linux guest OS, use LinuxPrep
            # https://pubs.vmware.com/vi3/sdk/ReferenceGuide/vim.vm.customization.LinuxPrep.html
            custom_spec.identity = vim.vm.customization.LinuxPrep()

            if 'domain' in self.params:
                custom_spec.identity.domain = str(self.params['domain'])

            custom_spec.identity.hostName = vim.vm.customization.FixedName()
            hostname = self.params.get('vm_hostname', None)
            if hostname is None:
                self.module.fail_json(msg="vm_hostname can not be None.")
            custom_spec.identity.hostName.name = hostname

        # Assign custom spec to custom item
        custom_item.spec = custom_spec
        try:
            if not self.module.check_mode:
                self.content.customizationSpecManager.CreateCustomizationSpec(custom_item)
            results['changed'] = True
        except (vim.fault.CannotDecryptPasswords, vim.fault.CustomizationFault) as custom_fault:
            self.module.fail_json(msg="Failed create custom specification '%s' using"
                                      " given parameter due to %s" % (self.spec_name,
                                                                      to_native(custom_fault.msg)))
        except vim.fault.AlreadyExists:
            pass
        except Exception as generic_exc:
            self.module.fail_json(msg="Failed create custom specification '%s' using"
                                      " given parameter due to generic exception : %s" % (self.spec_name,
                                                                                          to_native(generic_exc)))
        self.module.exit_json(**results)


def main():
    argument_spec = vmware_argument_spec()
    argument_spec.update(
        dict(
            spec_name=dict(type='str', required=True),
            new_spec_name=dict(type='str'),
            spec_description=dict(type='str'),
            spec_type=dict(type='str',
                           choices=['Linux', 'Windows'],
                           default='Linux'),
            networks=dict(type='list'),
            vm_hostname=dict(type='str'),
            dns_servers=dict(type='list'),
            dns_suffix=dict(type='list'),
            domain=dict(type='str'),
            state=dict(default='present',
                       choices=['present', 'absent'],
                       type='str'),

            # Windows specific
            fullname=dict(type='str', default='Administrator'),
            orgname=dict(type='str', default='ACME'),
            productid=dict(type='str'),
            autologon=dict(type='bool', default=False),
            autologoncount=dict(type='int', default=1),
            timezone=dict(type='str'),
            windows_password=dict(type='str', no_log=True),
            domainadmin=dict(type='str'),
            domainadminpassword=dict(type='str'),
            joindomain=dict(type='str'),
            joinworkgroup=dict(type='str', default='WORKGROUP'),
            runonce=dict(type='list', default=[]),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ['joinworkgroup', 'joindomain'],
        ],
        required_together=[
            ['domainadmin', 'domainadminpassword', 'joindomain'],
        ]
    )

    vmware_guest_customization = VmwareCustomizationMgr(module)
    vmware_guest_customization.process_state()


if __name__ == '__main__':
    main()
