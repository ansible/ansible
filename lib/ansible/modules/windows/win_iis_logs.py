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
description: Manages the IIS log configuration either per-site, or server wide
options:
    site_name:
        description: The name of the site for which logging should be configured.  Also accepted is "System" for system-wide logging.
        required: false
        default: 'System'
    log_directory:
        description: The target directory for IIS Logs
        required: false
        default: null
        type: string
    log_ext_file_flags:
        description: Built-In IIS Log fields to be included. This must be a list of objects with these properties: field_name, state.
        type: list
        required: false
    log_custom_fields:
        description: Custom log fileds to be included.  This must be a list of objects with these properties: field_name, source_type, source_name, state
        type: list
        required: false
    use_local_time:
        description: Whether or not to use local time for IIS log rotation.
        required: false
        type: bool

author:
    - Charles Crossan (@crossan007)
'''

EXAMPLES = r'''
# Ensure IIS logs to E:\Logs, with all built-in properties, and also including the RequestHeader 'X-Forwarded-For' as a log property.
  - name: Ensure IIS Site defaults are correct
    win_iis_logs:
      configuration: siteDefaults # not available when central_log_file_mode is _not_ "Site"
      site_log_format: "W3C"
      log_directory: '%SystemDrive%\\inetpub\\logs\\LogFiles'
      use_local_time: true
      log_ext_file_flags: all # Only available if format is W3C
      rotation_period: MaxSize
      truncate_size: 8675309
      log_custom_fields: # Only available if format is W3C
        - field_name: 'x-forwarded-for'
          source_type: 'RequestHeader'
          source_name:  'X-Forwarded-For'
          state: present

# Configure server-wide parameters.
  - name: Ensure IIS Logging is configured
    win_iis_logs:
      configuration: server
      central_log_file_mode: "Site" #Site, CentralBinary or CentralW3C are available
      log_in_utf8: false # true / false.  Only available for configuration: server
      log_directory: '%SystemDrive%\\inetpub\\logs\\LogFiles'
      use_local_time: true
      log_ext_file_flags: all # Only available if format is CentralW3C
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
