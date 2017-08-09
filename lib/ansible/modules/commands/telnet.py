# this is a virtual module that is entirely implemented server side
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: telnet
short_description: Executes a low-down and dirty telnet command
version_added: 2.4
description:
     - Executes a low-down and dirty telnet command, not going through the module subsystem.
     - This is mostly to be used for enabling ssh on devices that only have telnet enabled by default.
options:
  commands:
    description:
      - List of commands to be executed in the telnet session.
    required: True
  host:
    description:
        - The host/target on which to execute the command
    required: False
    default: remote_addr
  user:
    description:
        - The user for login
    required: False
    default: remote_user
  password:
    description:
        - The password for login
  port:
    description:
        - Remote port to use
    default: 23
  timeout:
    description:
        - timeout for remote operations
    default: 120
  command:
    description:
        - Command to execute in telnet session
    required: True
  pause:
    description:
        - Seconds to pause between each command issued
    required: False
    default: 1
notes:
    - The C(environment) keyword does not work with this task
author:
    - Ansible Core Team
'''

EXAMPLES = '''
- name: Force ssh on IOS
  telnet:
    command: transport input ssh
    user: cisco
    password: cisco
'''

RETURN= '''
output:
    description: output of each command is an element in this list
    type: list
    returned: always
    sample: [ 'success' ]

'''
