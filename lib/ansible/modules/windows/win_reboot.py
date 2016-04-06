DOCUMENTATION='''
---
module: win_reboot
short_description: Reboot a windows machine
description:
     - Reboot a Windows machine, wait for it to go down, come back up, and respond to commands.
version_added: "2.1"
options:
  pre_reboot_delay_sec:
    description:
    - Seconds for shutdown to wait before requesting reboot
    default: 2
  shutdown_timeout_sec:
    description:
    - Maximum seconds to wait for shutdown to occur
    - Increase this timeout for very slow hardware, large update applications, etc
    default: 600
  reboot_timeout_sec:
    description:
    - Maximum seconds to wait for machine to re-appear on the network and respond to a test command
    - This timeout is evaluated separately for both network appearance and test command success (so maximum clock time is actually twice this value)
    default: 600
  connect_timeout_sec:
    description:
    - Maximum seconds to wait for a single successful TCP connection to the WinRM endpoint before trying again
    default: 5
  test_command:
    description:
    - Command to expect success for to determine the machine is ready for management
    default: whoami
author:
    - Matt Davis (@nitzmahone)
'''

EXAMPLES='''
# unconditionally reboot the machine with all defaults
- win_reboot:

# apply updates and reboot if necessary
- win_updates:
  register: update_result
- win_reboot:
  when: update_result.reboot_required

# reboot a slow machine that might have lots of updates to apply
- win_reboot:
    shutdown_timeout_sec: 3600
    reboot_timeout_sec: 3600
'''

RETURNS='''
rebooted:
    description: true if the machine was rebooted
    returned: always
    type: boolean
    sample: true
'''
