#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_chocolatey_source
version_added: '2.7'
short_description: Manages Chocolatey sources
description:
- Used to managed Chocolatey sources configured on the client.
- Requires Chocolatey to be already installed on the remote host.
options:
  admin_only:
    description:
    - Makes the source visible to Administrators only.
    - Requires Chocolatey >= 0.10.8.
    - When creating a new source, this defaults to C(False).
    type: bool
  allow_self_service:
    description:
    - Allow the source to be used with self-service
    - Requires Chocolatey >= 0.10.4.
    - When creating a new source, this defaults to C(False).
    type: bool
  bypass_proxy:
    description:
    - Bypass the proxy when using this source.
    - Requires Chocolatey >= 0.10.4.
    - When creating a new source, this defaults to C(False).
    type: bool
  certificate:
    description:
    - The path to a .pfx file to use for X509 authenticated feeds.
    - Requires Chocolatey >= 0.9.10.
  certificate_password:
    description:
    - The password for I(certificate) if required.
    - Requires Chocolatey >= 0.9.10.
  name:
    description:
    - The name of the source to configure.
    required: yes
  priority:
    description:
    - The priority order of this source compared to other sources, lower is
      better.
    - All priorities above C(0) will be evaluated first, then zero-based values
      will be evaluated in config file order.
    - Requires Chocolatey >= 0.9.9.9.
    - When creating a new source, this defaults to C(0).
    type: int
  source:
    description:
    - The file/folder/url of the source.
    - Required when I(state) is C(present) or C(disabled).
  source_username:
    description:
    - The username used to access I(source).
  source_password:
    description:
    - The password for I(source_username).
    - Required if I(source_username) is set.
  state:
    description:
    - When C(absent), will remove the source.
    - When C(disabled), will ensure the source exists but is disabled.
    - When C(present), will ensure the source exists and is enabled.
    choices:
    - absent
    - disabled
    - present
    default: present
  update_password:
    description:
    - When C(always), the module will always set the password and report a
      change if I(certificate_password) or I(source_password) is set.
    - When C(on_create), the module will only set the password if the source
      is being created.
    choices:
    - always
    - on_create
    default: always
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: remove the default public source
  win_chocolatey_source:
    name: chocolatey
    state: absent

- name: add new internal source
  win_chocolatey_source:
    name: internal repo
    state: present
    source: http://chocolatey-server/chocolatey

- name: create HTTP source with credentials
  win_chocolatey_source:
    name: internal repo
    state: present
    source: https://chocolatey-server/chocolatey
    source_username: username
    source_password: password

- name: disable Chocolatey source
  win_chocolatey_source:
    name: chocoaltey
    state: disabled
'''

RETURN = r'''
'''
