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
short_description: Configures a IIS Web site binding
description:
     - Creates, removes and configures a binding to an existing IIS Web site.
options:
  name:
    description:
      - Names of web site.
    required: yes
    aliases: [ website ]
  state:
    description:
      - State of the binding.
    choices: [ absent, present ]
    default: present
  port:
    description:
      - The port to bind to / use for the new site.
    default: 80
  ip:
    description:
      - The IP address to bind to / use for the new site.
    default: '*'
  host_header:
    description:
      - The host header to bind to / use for the new site.
      - If you are creating/removing a catch-all binding, omit this parameter rather than defining it as '*'.
  protocol:
    description:
      - The protocol to be used for the Web binding (usually HTTP, HTTPS, or FTP).
    default: http
  certificate_hash:
    description:
      - Certificate hash (thumbprint) for the SSL binding. The certificate hash is the unique identifier for the certificate.
  certificate_store_name:
    description:
      - Name of the certificate store where the certificate for the binding is located.
    default: my
  ssl_flags:
    description:
      - This parameter is only valid on Server 2012 and newer.
      - Primarily used for enabling and disabling server name indication (SNI).
      - Set to c(0) to disable SNI.
      - Set to c(1) to enable SNI.
    version_added: "2.5"
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

- name: Remove the default http binding
  win_iis_webbinding:
    name: Default Web Site
    port: 80
    ip: '*'
    state: absent

- name: Add a HTTPS binding
  win_iis_webbinding:
    name: Default Web Site
    protocol: https
    port: 443
    ip: 127.0.0.1
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

RETURN = r'''
website_state:
  description:
    - The state of the website being targetted
    - Can be helpful in case you accidentally cause a binding collision
      which can result in the targetted site being stopped
  returned: always
  type: string
  sample: "Started"
  version_added: "2.5"
operation_type:
  description:
    - The type of operation performed
    - Can be removed, updated, matched, or added
  returned: on success
  type: string
  sample: "removed"
  version_added: "2.5"
binding_info:
  description:
    - Information on the binding being manipulated
  returned: on success
  type: dictionary
  sample: |-
    "binding_info": {
      "bindingInformation": "127.0.0.1:443:",
      "certificateHash": "FF3910CE089397F1B5A77EB7BAFDD8F44CDE77DD",
      "certificateStoreName": "MY",
      "hostheader": "",
      "ip": "127.0.0.1",
      "port": 443,
      "protocol": "https",
      "sslFlags": "not supported"
    }
  version_added: "2.5"
'''
