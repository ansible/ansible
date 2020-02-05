#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, AMTEGA - Xunta de Galicia
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_domain_computer
short_description: Manage computers in Active Directory
description:
  - Create, read, update and delete computers in Active Directory using a
    windows bridge computer to launch New-ADComputer, Get-ADComputer,
    Set-ADComputer, Remove-ADComputer and Move-ADObject powershell commands.
version_added: '2.6'
options:
  name:
    description:
      - Specifies the name of the object.
      - This parameter sets the Name property of the Active Directory object.
      - The LDAP display name (ldapDisplayName) of this property is name.
    type: str
    required: true
  sam_account_name:
    description:
      - Specifies the Security Account Manager (SAM) account name of the
        computer.
      - It maximum is 256 characters, 15 is advised for older
        operating systems compatibility.
      - The LDAP display name (ldapDisplayName) for this property is sAMAccountName.
      - If ommitted the value is the same as C(name).
      - Note that all computer SAMAccountNames need to end with a $.
    type: str
  enabled:
    description:
      - Specifies if an account is enabled.
      - An enabled account requires a password.
      - This parameter sets the Enabled property for an account object.
      - This parameter also sets the ADS_UF_ACCOUNTDISABLE flag of the
        Active Directory User Account Control (UAC) attribute.
    type: bool
    default: yes
  ou:
    description:
      - Specifies the X.500 path of the Organizational Unit (OU) or container
        where the new object is created. Required when I(state=present).
    type: str
  description:
    description:
      - Specifies a description of the object.
      - This parameter sets the value of the Description property for the object.
      - The LDAP display name (ldapDisplayName) for this property is description.
    type: str
    default: ''
  dns_hostname:
    description:
      - Specifies the fully qualified domain name (FQDN) of the computer.
      - This parameter sets the DNSHostName property for a computer object.
      - The LDAP display name for this property is dNSHostName.
      - Required when I(state=present).
    type: str
  domain_username:
    description:
    - The username to use when interacting with AD.
    - If this is not set then the user Ansible used to log in with will be
      used instead when using CredSSP or Kerberos with credential delegation.
    type: str
    version_added: '2.8'
  domain_password:
    description:
    - The password for I(username).
    type: str
    version_added: '2.8'
  domain_server:
    description:
    - Specifies the Active Directory Domain Services instance to connect to.
    - Can be in the form of an FQDN or NetBIOS name.
    - If not specified then the value is based on the domain of the computer
      running PowerShell.
    type: str
    version_added: '2.8'
  state:
    description:
      - Specified whether the computer should be C(present) or C(absent) in
        Active Directory.
    type: str
    choices: [ absent, present ]
    default: present
seealso:
- module: win_domain
- module: win_domain_controller
- module: win_domain_group
- module: win_domain_membership
- module: win_domain_user
author:
- Daniel Sánchez Fábregas (@Daniel-Sanchez-Fabregas)
'''

EXAMPLES = r'''
  - name: Add linux computer to Active Directory OU using a windows machine
    win_domain_computer:
      name: one_linux_server.my_org.local
      sam_account_name: linux_server$
      dns_hostname: one_linux_server.my_org.local
      ou: "OU=servers,DC=my_org,DC=local"
      description: Example of linux server
      enabled: yes
      state: present
    delegate_to: my_windows_bridge.my_org.local

  - name: Remove linux computer from Active Directory using a windows machine
    win_domain_computer:
      name: one_linux_server.my_org.local
      state: absent
    delegate_to: my_windows_bridge.my_org.local
'''

RETURN = r'''
'''
