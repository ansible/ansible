#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_shutdown
short_description: Shutdown a windows machine
description:
- Extension of the reboot class
- Shutdown a Windows machine
- For non-Windows targets, use the M(shutdown) module instead.
version_added: '2.8'
options:
  pre_reboot_delay:
    description:
    - Seconds to wait before reboot. Passed as a parameter to the reboot command.
    type: int
    default: 2
    aliases: [ pre_reboot_delay_sec ]
  post_reboot_delay:
    description:
    - Seconds to wait after the reboot command was successful before attempting to validate the system rebooted successfully.
    - This is useful if you want wait for something to settle despite your connection already working.
    type: int
    default: 0
    version_added: '2.4'
    aliases: [ post_reboot_delay_sec ]
  shutdown_timeout:
    description:
    - Maximum seconds to wait for shutdown to occur.
    - Increase this timeout for very slow hardware, large update applications, etc.
    - This option has been removed since Ansible 2.5 as the win_reboot behavior has changed.
    type: int
    default: 600
    aliases: [ shutdown_timeout_sec ]
  reboot_timeout:
    description:
    - Maximum seconds to wait for machine to re-appear on the network and respond to a test command.
    - This timeout is evaluated separately for both reboot verification and test command success so maximum clock time is actually twice this value.
    type: int
    default: 600
    aliases: [ reboot_timeout_sec ]
  connect_timeout:
    description:
    - Maximum seconds to wait for a single successful TCP connection to the WinRM endpoint before trying again.
    type: int
    default: 5
    aliases: [ connect_timeout_sec ]
  test_command:
    description:
    - Command to expect success for to determine the machine is ready for management.
    type: str
    default: whoami
  msg:
    description:
    - Message to display to users.
    type: str
    default: Reboot initiated by Ansible
notes:
- If a shutdown was already scheduled on the system, C(win_reboot) will abort the scheduled shutdown and enforce its own shutdown.
- The connection user must have the C(SeRemoteShutdownPrivilege) privilege enabled, see
  U(https://docs.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/force-shutdown-from-a-remote-system)
  for more information.
seealso:
- module: reboot
- module: shutdown
- module: win_reboot
author:
- Marco Marinello (@mmaridev)
'''

EXAMPLES = r'''
- name: Shutdown the machine with all defaults
  win_shutdown:
'''
