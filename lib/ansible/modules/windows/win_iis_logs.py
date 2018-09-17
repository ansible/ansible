#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_iis_logs
version_added: "2.8"
short_description: Manages IIS Log configuration
description:
  - "Manages the IIS log configuration either per-site, or server wide"
options:
  configuration:
    description:
      - "This module supports configuring logging for the C(server), C(siteDefaults), or one C(site)"
    required: true
    default: server
  site_name:
    description:
      - "The name of the site for which logging should be configured."
      - "Only applies when C(configuration) is set to C(site).
    required: false
    default: 'System'
  log_directory:
    description: The target directory for IIS Logs.
    required: false
    default: null
    type: str
  site_log_format:
    description:  Log file format.  Only applies when C(configuration) is C(site) or C(siteDefaults)
    required: false
    default: null
  log_ext_file_flags:
    description:
      - "Built-In IIS Log fields to be included."
      - "Objects in this list must have these properties: field_name, state."
    type: list
    required: false
  log_custom_fields:
    description:
      - "Custom log fileds to be included.  Only applies when C(configuration) is C(site) or C(siteDefaults)"
      - "Objects in this list must have these properties:"
      - "field_name, source_type, source_name, state"
    type: list
    required: false
  use_local_time:
    description: Whether or not to use local time for IIS log rotation.
    required: false
    type: bool
  rotation_period:
    description: 
      - "specifies log rotation period."
      - "valid values include C(Hourly),C(Daily),C(Weekly),C(Monthly),C(MaxSize),C(Disabled)
    required: false
    default: null
  truncate_size:
    description: when C(rotation_period) is C(MaxSize), this specifies the size in bytes at which logs are rotated
    required: false
    default: null
  central_log_file_mode:
    description: 
      - "when C(configuration) is C(server), this specifies the global logging configuration mechanism."
      - "C(CentralBinary), C(CentralW3C), 
    required: false
    default: null
  log_in_utf8:
    description: specifies whether to log in UTF-8 mode C(true) or ANSI mode C(false)
    required: false
    default: null

author:
  - Charles Crossan (@crossan007)
'''

EXAMPLES = r'''
# Ensure IIS logs to E:\Logs, with all built-in properties, and also including the RequestHeader 'X-Forwarded-For' as a log property.
  - name: Ensure IIS Logging is configured
    win_iis_logs:
      site_name: "System"
      log_directory: "E:\\Logs"
      use_local_time: true
      log_ext_file_flags: all
      log_custom_fields:
        - field_name: 'x-forwarded-for'
          source_type: 'RequestHeader'
          source_name:  'X-Forwarded-For'
          state: present

# Rotate logs at truncation intervals
  - name: Ensure IIS Logging is configured
    win_iis_logs:
        site_name: "System"
        log_directory: '%SystemDrive%\\inetpub\\logs\\LogFiles'
        use_local_time: false
        log_ext_file_flags: all
        rotation_period: MaxSize
        truncate_size: 8675309

'''

RETURN = r'''
msg:
    description: what was done
    returned: always
    type: string
    sample: "CustomFields, LogDirectory, Use Local Time changed"
'''
