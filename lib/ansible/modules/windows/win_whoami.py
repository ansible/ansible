#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_whoami
version_added: "2.5"
short_description: Get information about the current user and process
description:
- Designed to return the same information as the C(whoami /all) command.
- Also includes information missing from C(whoami) such as logon metadata like
  logon rights, id, type.
notes:
- If running this module with a non admin user, the logon rights will be an
  empty list as Administrator rights are required to query LSA for the
  information.
seealso:
- module: win_credential
- module: win_group_membership
- module: win_user_right
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: Get whoami information
  win_whoami:
'''

RETURN = r'''
authentication_package:
  description: The name of the authentication package used to authenticate the
    user in the session.
  returned: success
  type: str
  sample: Negotiate
user_flags:
  description: The user flags for the logon session, see UserFlags in
    U(https://msdn.microsoft.com/en-us/library/windows/desktop/aa380128).
  returned: success
  type: str
  sample: Winlogon
upn:
  description: The user principal name of the current user.
  returned: success
  type: str
  sample: Administrator@DOMAIN.COM
logon_type:
  description: The logon type that identifies the logon method, see
    U(https://msdn.microsoft.com/en-us/library/windows/desktop/aa380129.aspx).
  returned: success
  type: str
  sample: Network
privileges:
  description: A dictionary of privileges and their state on the logon token.
  returned: success
  type: dict
  sample: {
      "SeChangeNotifyPrivileges": "enabled-by-default",
      "SeRemoteShutdownPrivilege": "disabled",
      "SeDebugPrivilege": "enabled"
  }
label:
  description: The mandatory label set to the logon session.
  returned: success
  type: complex
  contains:
    domain_name:
      description: The domain name of the label SID.
      returned: success
      type: str
      sample: Mandatory Label
    sid:
      description: The SID in string form.
      returned: success
      type: str
      sample: S-1-16-12288
    account_name:
      description: The account name of the label SID.
      returned: success
      type: str
      sample: High Mandatory Level
    type:
      description: The type of SID.
      returned: success
      type: str
      sample: Label
impersonation_level:
  description: The impersonation level of the token, only valid if
    C(token_type) is C(TokenImpersonation), see
    U(https://msdn.microsoft.com/en-us/library/windows/desktop/aa379572.aspx).
  returned: success
  type: str
  sample: SecurityAnonymous
login_time:
  description: The logon time in ISO 8601 format
  returned: success
  type: str
  sample: '2017-11-27T06:24:14.3321665+10:00'
groups:
  description: A list of groups and attributes that the user is a member of.
  returned: success
  type: list
  sample: [
      {
          "account_name": "Domain Users",
          "domain_name": "DOMAIN",
          "attributes": [
              "Mandatory",
              "Enabled by default",
              "Enabled"
          ],
          "sid": "S-1-5-21-1654078763-769949647-2968445802-513",
          "type": "Group"
      },
      {
          "account_name": "Administrators",
          "domain_name": "BUILTIN",
          "attributes": [
              "Mandatory",
              "Enabled by default",
              "Enabled",
              "Owner"
          ],
          "sid": "S-1-5-32-544",
          "type": "Alias"
      }
  ]
account:
  description: The running account SID details.
  returned: success
  type: complex
  contains:
    domain_name:
      description: The domain name of the account SID.
      returned: success
      type: str
      sample: DOMAIN
    sid:
      description: The SID in string form.
      returned: success
      type: str
      sample: S-1-5-21-1654078763-769949647-2968445802-500
    account_name:
      description: The account name of the account SID.
      returned: success
      type: str
      sample: Administrator
    type:
      description: The type of SID.
      returned: success
      type: str
      sample: User
login_domain:
  description: The name of the domain used to authenticate the owner of the
    session.
  returned: success
  type: str
  sample: DOMAIN
rights:
  description: A list of logon rights assigned to the logon.
  returned: success and running user is a member of the local Administrators group
  type: list
  sample: [
      "SeNetworkLogonRight",
      "SeInteractiveLogonRight",
      "SeBatchLogonRight",
      "SeRemoteInteractiveLogonRight"
  ]
logon_server:
  description: The name of the server used to authentcate the owner of the
    logon session.
  returned: success
  type: str
  sample: DC01
logon_id:
  description: The unique identifier of the logon session.
  returned: success
  type: int
  sample: 20470143
dns_domain_name:
  description: The DNS name of the logon session, this is an empty string if
    this is not set.
  returned: success
  type: str
  sample: DOMAIN.COM
token_type:
  description: The token type to indicate whether it is a primary or
    impersonation token.
  returned: success
  type: str
  sample: TokenPrimary
'''
