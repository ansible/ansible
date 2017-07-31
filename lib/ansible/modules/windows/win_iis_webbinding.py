#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Henrik Wallström <henrik@wallstroms.nu>
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


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_iis_webbinding
version_added: "2.0"
short_description: Configures a IIS Web site.
description:
     - Creates, Removes and configures a binding to an existing IIS Web site
options:
  name:
    description:
      - Names of web site
    required: true
    default: null
    aliases: []
  state:
    description:
      - State of the binding
    choices:
      - present
      - absent
    required: false
    default: null
    aliases: []
  port:
    description:
      - The port to bind to / use for the new site.
    required: false
    default: null
    aliases: []
  ip:
    description:
      - The IP address to bind to / use for the new site.
    required: false
    default: null
    aliases: []
  host_header:
    description:
      - The host header to bind to / use for the new site.
    required: false
    default: null
    aliases: []
  protocol:
    description:
      - The protocol to be used for the Web binding (usually HTTP, HTTPS, or FTP).
    required: false
    default: null
    aliases: []
  certificate_hash:
    description:
      - Certificate hash for the SSL binding. The certificate hash is the unique identifier for the certificate.
    required: false
    default: null
    aliases: []
  certificate_store_name:
    description:
      -  Name of the certificate store where the certificate for the binding is located.
    required: false
    default: "My"
    aliases: []
author: Henrik Wallström
'''

EXAMPLES = r'''
- name: Return binding information for an existing host
  win_iis_webbinding:
    name: Default Web Site

- name: Return the HTTPS binding information for an existing host
  win_iis_webbinding:
    name: Default Web Site
    protocol: https

- name: Add a HTTP binding on port 9090
  win_iis_webbinding:
    name: Default Web Site
    port: 9090
    state: present

- name: Remove the HTTP binding on port 9090
  win_iis_webbinding:
    name: Default Web Site
    port: 9090
    state: absent

- name: Add a HTTPS binding
  win_iis_webbinding:
    name: Default Web Site
    protocol: https
    state: present

- name: Add a HTTPS binding and select certificate to use
  win_iis_webbinding:
    name: Default Web Site
    protocol: https
    certificate_hash: B0D0FA8408FC67B230338FCA584D03792DA73F4C
    state: present

- name: Website https biding to specific port
  win_iis_webbinding:
    name: Default Web Site
    protocol: https
    port: 443
    certificate_hash: D1A3AF8988FD32D1A3AF8988FD323792DA73F4C
    state: present
'''
