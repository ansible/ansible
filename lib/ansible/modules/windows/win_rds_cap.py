#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Kevin Subileau (@ksubileau)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_rds_cap
short_description: Manage Connection Authorization Policies (CAP) on a Remote Desktop Gateway server
description:
  - Creates, removes and configures a Remote Desktop connection authorization policy (RD CAP).
  - A RD CAP allows you to specify the users who can connect to a Remote Desktop Gateway server.
version_added: "2.8"
author:
  - Kevin Subileau (@ksubileau)
options:
  name:
    description:
      - Name of the connection authorization policy.
    type: str
    required: yes
  state:
    description:
      - The state of connection authorization policy.
      - If C(absent) will ensure the policy is removed.
      - If C(present) will ensure the policy is configured and exists.
      - If C(enabled) will ensure the policy is configured, exists and enabled.
      - If C(disabled) will ensure the policy is configured, exists, but disabled.
    type: str
    choices: [ absent, enabled, disabled, present ]
    default: present
  auth_method:
    description:
      - Specifies how the RD Gateway server authenticates users.
      - When a new CAP is created, the default value is C(password).
    type: str
    choices: [ both, none, password, smartcard ]
  order:
    description:
      - Evaluation order of the policy.
      - The CAP in which I(order) is set to a value of '1' is evaluated first.
      - By default, a newly created CAP will take the first position.
      - If the given value exceed the total number of existing policies,
        the policy will take the last position but the evaluation order
        will be capped to this number.
    type: int
  session_timeout:
    description:
      - The maximum time, in minutes, that a session can be idle.
      - A value of zero disables session timeout.
    type: int
  session_timeout_action:
    description:
      - The action the server takes when a session times out.
      - 'C(disconnect): disconnect the session.'
      - 'C(reauth): silently reauthenticate and reauthorize the session.'
    type: str
    choices: [ disconnect, reauth ]
    default: disconnect
  idle_timeout:
    description:
      - Specifies the time interval, in minutes, after which an idle session is disconnected.
      - A value of zero disables idle timeout.
    type: int
  allow_only_sdrts_servers:
    description:
      - Specifies whether connections are allowed only to Remote Desktop Session Host servers that
        enforce Remote Desktop Gateway redirection policy.
    type: bool
  user_groups:
    description:
      - A list of user groups that is allowed to connect to the Remote Gateway server.
      - Required when a new CAP is created.
    type: list
  computer_groups:
    description:
      - A list of computer groups that is allowed to connect to the Remote Gateway server.
    type: list
  redirect_clipboard:
    description:
      - Allow clipboard redirection.
    type: bool
  redirect_drives:
    description:
      - Allow disk drive redirection.
    type: bool
  redirect_printers:
    description:
      - Allow printers redirection.
    type: bool
  redirect_serial:
    description:
      - Allow serial port redirection.
    type: bool
  redirect_pnp:
    description:
      - Allow Plug and Play devices redirection.
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
- name: Create a new RDS CAP with a 30 minutes timeout and clipboard redirection enabled
  win_rds_cap:
    name: My CAP
    user_groups:
      - BUILTIN\users
    session_timeout: 30
    session_timeout_action: disconnect
    allow_only_sdrts_servers: yes
    redirect_clipboard: yes
    redirect_drives: no
    redirect_printers: no
    redirect_serial: no
    redirect_pnp: no
    state: enabled
'''

RETURN = r'''
'''
