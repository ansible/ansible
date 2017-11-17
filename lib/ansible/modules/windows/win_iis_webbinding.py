#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# Copyright: (c) 2017, Henrik Wallström <henrik@wallstroms.nu>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: win_iis_webbinding
version_added: "2.0"
short_description: Configures a IIS Web site binding.
description:
     - Creates, Removes and configures a binding to an existing IIS Web site
options:
  name:
    description:
      - Names of web site
    required: true
    default: null
    aliases: website
  state:
    description:
      - State of the binding
    choices:
      - present
      - absent
    required: false
    default: present
  port:
    description:
      - The port to bind to / use for the new site.
    required: false
    default: 80
  ip:
    description:
      - The IP address to bind to / use for the new site.
    required: false
    default: '*'
  host_header:
    description:
      - The host header to bind to / use for the new site.
    required: false
  protocol:
    description:
      - The protocol to be used for the Web binding (usually HTTP, HTTPS, or FTP).
    required: false
    default: http
  certificate_hash:
    description:
      - Certificate hash (thumbprint) for the SSL binding. The certificate hash is the unique identifier for the certificate.
    required: false
  certificate_store_name:
    description:
      - Name of the certificate store where the certificate for the binding is located.
    required: false
    default: "my"
  ssl_flags:
    description:
      - This parameter is only valid on Server 2012 and newer.
      - Primarily used for enabling and disabling server name indication (SNI).
      - Set to 0 to disable SNI.
      - Set to 1 to enable SNI.
author:
  - Noah Sparks (@nwsparks)
  - Henrik Wallström
'''

EXAMPLES = r'''
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
    certificate_hash: B0D0FA8408FC67B230338FCA584D03792DA73F4C
    state: present

- name: Add a HTTPS binding with host header and SNI enabled
  win_iis_webbinding:
    name: Default Web Site
    protocol: https
    port: 443
    host_header: test.com
    ssl_flags: 1
    certificate_hash: D1A3AF8988FD32D1A3AF8988FD323792DA73F4C
    state: present
'''
