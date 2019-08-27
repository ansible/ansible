#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Subileau (@ksubileau)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_rds_settings
short_description: Manage main settings of a Remote Desktop Gateway server
description:
  - Configure general settings of a Remote Desktop Gateway server.
version_added: "2.8"
author:
  - Kevin Subileau (@ksubileau)
options:
  certificate_hash:
    description:
      - Certificate hash (thumbprint) for the Remote Desktop Gateway server. The certificate hash is the unique identifier for the certificate.
    type: str
  max_connections:
    description:
      - The maximum number of connections allowed.
      - If set to C(0), no new connections are allowed.
      - If set to C(-1), the number of connections is unlimited.
    type: int
  ssl_bridging:
    description:
      - Specifies whether to use SSL Bridging.
      - 'C(none): no SSL bridging.'
      - 'C(https_http): HTTPS-HTTP bridging.'
      - 'C(https_https): HTTPS-HTTPS bridging.'
    type: str
    choices: [ https_http, https_https, none ]
  enable_only_messaging_capable_clients:
    description:
      - If enabled, only clients that support logon messages and administrator messages can connect.
    type: bool
requirements:
  - Windows Server 2008R2 (6.1) or higher.
  - The Windows Feature "RDS-Gateway" must be enabled.
seealso:
- module: win_rds_cap
- module: win_rds_rap
- module: win_rds_settings
'''

EXAMPLES = r'''
- name: Configure the Remote Desktop Gateway
  win_rds_settings:
    certificate_hash: B0D0FA8408FC67B230338FCA584D03792DA73F4C
    max_connections: 50
  notify:
    - Restart TSGateway service
'''

RETURN = r'''
'''
