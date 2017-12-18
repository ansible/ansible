#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2017, Jamie Thompson <jamiet@datacom.co.nz>
# (c) 2017, Michael Eaton <meaton@iforium.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.2',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_firewall
version_added: '2.4'
short_description: Enable or disable the Windows Firewall
description:
- Enable or Disable Windows Firewall profiles.
options:
  profiles:
    description:
    - Specify one or more profiles to change.
    choices:
    - Domain
    - Private
    - Public
    default: [Domain, Private, Public]
  state:
    description:
    - Set state of firewall for given profile.
    choices:
    - enabled
    - disabled
  defaultinboundaction:
    description:
    - Specifies how to filter inbound traffic.
    choices:
    - block
    - allow
    - notconfigured
  defaultoutboundaction:
    description:
    - Specifies how to filter outbound traffic.
    choices:
    - block
    - allow
    - notconfigured
  allowinboundrules:
    description:
    - Specifies that the firewall blocks inbound traffic.
    choices:
    - true
    - false
    - notconfigured
  allowlocalfirewallrules:
    description:
    - Specifies that the local firewall rules should be merged into the effective policy along with Group Policy settings.
    choices:
    - true
    - false
    - notconfigured
  allowlocalipsecrules:
    description:
    - Specifies that the local IPsec rules should be merged into the effective policy along with Group Policy settings.
    choices:
    - true
    - false
    - notconfigured
  allowuserapps:
    description:
    - Specifies that the local IPsec rules should be merged into the effective policy along with Group Policy settings.
    choices:
    - true
    - false
    - notconfigured
  allowuserports:
    description:
    - Determines how the Windows XP policy is applied to the newer Windows Firewall. Defines how to use the policy merge field for older operating systems.
    choices:
    - true
    - false
    - notconfigured
  allowunicastresponsetomulticast:
    description:
    - Allows unicast responses to multi-cast traffic.
    choices:
    - true
    - false
    - notconfigured
  notifyonlisten:
    description:
    - Allows the notification of listening for inbound connections by a service.
    choices:
    - true
    - false
    - notconfigured
  enablestealthmodeforipsec:
    description:
    - Enables stealth mode for IPsec traffic.
    choices:
    - true
    - false
    - notconfigured
  logfilename:
    description:
    - Specifies the path and filename of the file to which Windows Server writes log entries.
    - '%windir%\system32\logfiles\firewall\pfirewall.log'
  logmaxsizekilobytes:
    description:
    - Specifies the maximum file size of the log, in kilobytes. The acceptable values for this parameter are: 1 through 32767
  logallowed:
    description:
    - Specifies how to log the allowed packets in the location specified by the LogFileName parameter.
    choices:
    - true
    - false
    - notconfigured
  logblocked:
    description:
    - Specifies how to log the dropped packets in the location specified by the LogFileName parameter.
    choices:
    - true
    - false
    - notconfigured
  logignored:
    description:
    - Specifies how to log the ignored packets in the location specified by the LogFileName parameter.
    choices:
    - true
    - false
    - notconfigured
requirements:
  - This module requires Windows Management Framework 5 or later.
author: Michael Eaton (@if-meaton)
'''

EXAMPLES = r'''
- name: Enable firewall for Domain, Public and Private profiles
  win_firewall:
    state: enabled
    profiles:
    - Domain
    - Private
    - Public
  tags: enable_firewall

- name: Disable Domain firewall
  win_firewall:
    state: disabled
    profiles:
    - Domain
  tags: disable_firewall

- name: Apply Domain Firewall settings
  win_firewall:
    profiles: Domain
    state: enabled
    defaultinboundaction: block
    defaultoutboundaction: allow
    notifyonlisten: true
    allowlocalfirewallrules: true
    allowlocalipsecrules: true
    logblocked: true
    logallowed: true
    logmaxsizekilobytes: 16364
    logfilename: "%systemroot%\\system32\\logfiles\\firewall\\domainfw.log"
'''

RETURN = r'''
enabled:
    description: current firewall status for chosen profile (after any potential change)
    returned: always
    type: bool
    sample: true
profiles:
    description: chosen profile
    returned: always
    type: string
    sample: Domain
state:
    description: desired state of the given firewall profile(s)
    returned: always
    type: list
    sample: enabled
msg:
    description: Possible error message on failure
    returned: failed
    type: string
    sample: "an error occurred when attempting to change firewall status for profile <profilename>"
'''
