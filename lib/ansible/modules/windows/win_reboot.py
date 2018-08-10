#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: win_reboot
short_description: Reboot a windows machine
description:
     - Reboot a Windows machine, wait for it to go down, come back up, and respond to commands.
version_added: "2.1"
options:
  pre_reboot_delay:
    description:
    - Seconds for shutdown to wait before requesting reboot
    type: int
    default: 2
    aliases: [ pre_reboot_delay_sec ]
  post_reboot_delay:
    description:
    - Seconds to wait after the reboot was successful and the connection was re-established
    - This is useful if you want wait for something to settle despite your connection already working
    type: int
    default: 0
    version_added: '2.4'
    aliases: [ post_reboot_delay_sec ]
  shutdown_timeout:
    description:
    - Maximum seconds to wait for shutdown to occur
    - Increase this timeout for very slow hardware, large update applications, etc
    - This option has been removed since Ansible 2.5 as the win_reboot behavior has changed
    type: int
    default: 600
    aliases: [ shutdown_timeout_sec ]
  reboot_timeout:
    description:
    - Maximum seconds to wait for machine to re-appear on the network and respond to a test command
    - This timeout is evaluated separately for both network appearance and test command success (so maximum clock time is actually twice this value)
    type: int
    default: 600
    aliases: [ reboot_timeout_sec ]
  connect_timeout:
    description:
    - Maximum seconds to wait for a single successful TCP connection to the WinRM endpoint before trying again
    type: int
    default: 5
    aliases: [ connect_timeout_sec ]
  test_command:
    description:
    - Command to expect success for to determine the machine is ready for management
    default: whoami
  msg:
    description:
    - Message to display to users
    default: Reboot initiated by Ansible
notes:
- If a shutdown was already scheduled on the system, C(win_reboot) will abort the scheduled shutdown and enforce its own shutdown.
author:
    - Matt Davis (@nitzmahone)
'''

EXAMPLES = r'''
# Unconditionally reboot the machine with all defaults
- win_reboot:

# Apply updates and reboot if necessary
- win_updates:
  register: update_result
- win_reboot:
  when: update_result.reboot_required

# Reboot a slow machine that might have lots of updates to apply
- win_reboot:
    reboot_timeout: 3600
'''

RETURN = r'''
rebooted:
  description: true if the machine was rebooted
  returned: always
  type: boolean
  sample: true
elapsed:
  description: The number of seconds that elapsed waiting for the system to be rebooted.
  returned: always
  type: int
  sample: 23
'''
