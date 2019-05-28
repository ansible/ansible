#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'core'
}

DOCUMENTATION = r'''
---
module: win_powerstate
short_description: Changes power state of a windows machine
description:
- Shutdown, Suspend or Hibernate a Windows machine.
version_added: '2.9'
requirements:
  - This module requires Windows Forms.
options:
  state:
    description:
    - A PowerState indicating the power activity mode to which to transition.
    type: str
    default: suspend
    choices: [ suspend, hibernate, shutdown ]
  force:
    description:
    - If set to C(true), force the power mode immediately.
    - If set to C(false), to cause Windows to send a power state change
      request to every application.
    type: bool
    default: false
  disablewake:
    description:
    - If set to C(true), disables restoring the system's power status to
      active on a wake event.
    - If set to C(false), enables restoring the system's power status to
      active on a wake event.
    type: bool
    default: true
notes:
- If an application does not respond to a suspend request within 20 seconds, Windows determines
  that it is in a non-responsive state, and that the application can either be put to sleep or
  terminated. Once an application responds to a suspend request, however, it can take whatever
  time it needs to clean up resources and shut down active processes.
- The connection user must have the C(SeRemoteShutdownPrivilege) privilege enabled, see
  U(https://docs.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/force-shutdown-from-a-remote-system)
  for more information.
- Suspend and hibernate states are not supported on Windows Server.
seealso:
- module: win_reboot
author:
- Jose Angel Munoz (@imjoseangel)
'''

EXAMPLES = r'''
- name: Suspends the machine with all defaults
  win_powerstate:

- name: Forces the shutdown of a machine
  win_powerstate:
    state: shutdown
    force: true

- name: Disables restoring from hibernated to active on a wake event
  win_powerstate:
    state: hibernate
    disablewake: true
'''

RETURN = r'''
changed:
  description: True if the machine state was changed.
  returned: always
  type: bool
  sample: true
module_args:
  description: The arguments passed to the module.
  returned: always
  type: dict
  sample: { "disablewake": true, "force": false, "state": "shutdown"}
'''
