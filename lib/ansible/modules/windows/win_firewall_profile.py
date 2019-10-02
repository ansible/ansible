#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Simon Lecoq <simon.lecoq@live.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: win_firewall_profile
version_added: "2.10"
short_description: Windows firewall profile default action automation
description:
  - Allows you to update settings for Windows firewall profiles default action.
options:
  profiles:
    description:
      - The profiles which need to be configured.
    type: list
    choices: [ Domain, Private, Public ]
    default: [ Domain, Private, Public ]
    aliases:
      - profile
  enabled:
    description:
      - Enabled or disable given profiles.
    type: str
    choices: [ True, False, NotConfigured ]
  default_inbound_action:
    description:
      - Default inbound action for given profiles.
    type: str
    choices: [ Allow, Block, NotConfigured ]
    aliases:
      - inbound
  default_outbound_action:
    description:
      - Default outbound action for given profiles.
    type: str
    choices: [ Allow, Block, NotConfigured ]
    aliases:
      - outbound
  log_file_name:
    description:
      - Specifies the path and filename of the file to which Windows writes log entries.
    type: path
    aliases:
      - log_file
  log_max_size_kilobytes:
    description:
      - Specifies the maximum file size of the log, in kilobytes (the acceptable values for this parameter are 1 through 32767).
    type: int
    aliases:
      - log_max_size
  log_allowed:
    description:
      - Specifies how to log the allowed packets.
    type: str
    choices: [ True, False, NotConfigured ]
  log_blocked:
    description:
      - Specifies how to log the dropped packets.
    type: str
    choices: [ True, False, NotConfigured ]
  log_ignored:
    description:
      - Specifies how to log the ignored packets.
    type: str
    choices: [ True, False, NotConfigured ]
seealso:
  - module: win_firewall_rule
  - module: win_firewall
author:
  - Simon Lecoq (@lowlighter)
'''

EXAMPLES = r'''
- name: Block inbound and outbound connections by default for Domain, Private and Public profiles
  win_firewall_profile:
    inbound: Block
    outbound: Block
    profiles:
      - Domain
      - Private
      - Public

- name: Reset inbound and outbound default action to Group policy for all profiles
  win_firewall_profile:
    inbound: NotConfigured
    outbound: NotConfigured

- name: Configure logs for all profiles (log blocked and ignored packets and set custom path for log)
  win_firewall_profile:
    log_file_name: "C:/path/to/firewall.log"
    log_allowed: False
    log_blocked: True
    log_ignored: True
    log_max_size: 2048

- name: Retrieve current profile configuration for Private and Public profiles
  win_firewall_profile:
  profiles:
    - Private
    - Public
  register: win_firewall_profiles_current_settings

- name: Enable all profiles
  win_firewall_profile:
    enabled: True
'''

RETURN = r'''
changed:
  description: Tell if one of given profile settings has changed.
  returned: always
  type: bool

profile:
  description: Contains current profile settings.
  returned: For each given profile
  type: complex
  contains:
    changed:
      description: Profile has changed.
      type: bool
    enabled:
      description: Enabled status.
      type: str
    default_inbound_action:
      description: Default inbound action.
      type: str
    default_outbound_action:
      description: Default outbound action.
      type: str
    log_file_name:
      description: Path and filename of the file to which Windows writes log entries.
      type: str
    log_max_size_kilobytes:
      description: Maximum file size of the log, in kilobytes.
      type: int
    log_allowed:
      description: Specifies how the allowed packets are logged.
      type: str
    log_blocked:
      description: Specifies how the dropped packets are logged.
      type: str
    log_ignored:
      description: Specifies how the ignored packets are logged.
      type: str
'''
