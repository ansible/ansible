# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = """
---
module: pause
short_description: Pause playbook execution
description:
  - Pauses playbook execution for a set amount of time, or until a prompt is acknowledged.
    All parameters are optional. The default behavior is to pause with a prompt.
  - To pause/wait/sleep per host, use the M(ansible.builtin.wait_for) module.
  - You can use C(ctrl+c) if you wish to advance a pause earlier than it is set to expire or if you need to abort a playbook run entirely.
    To continue early press C(ctrl+c) and then C(c). To abort a playbook press C(ctrl+c) and then C(a).
  - Prompting for a set amount of time is not supported. Pausing playbook execution is interruptible but does not return user input.
  - The pause module integrates into async/parallelized playbooks without any special considerations (see Rolling Updates).
    When using pauses with the C(serial) playbook parameter (as in rolling updates) you are only prompted once for the current group of hosts.
  - This module is also supported for Windows targets.
version_added: "0.8"
options:
  minutes:
    description:
      - A positive number of minutes to pause for.
  seconds:
    description:
      - A positive number of seconds to pause for.
  prompt:
    description:
      - Optional text to use for the prompt message.
      - User input is only returned if O(seconds) and O(minutes) are both not specified,
        otherwise this is just a custom message before playbook execution is paused.
  echo:
    description:
      - Controls whether or not keyboard input is shown when typing.
      - Only has effect if neither O(seconds) nor O(minutes) are set.
    type: bool
    default: 'yes'
    version_added: 2.5
author: "Tim Bielawa (@tbielawa)"
extends_documentation_fragment:
  -  action_common_attributes
  -  action_common_attributes.conn
  -  action_common_attributes.flow
attributes:
    action:
        support: full
    async:
        support: none
    become:
        support: none
    bypass_host_loop:
        support: full
    check_mode:
        support: full
    connection:
        support: none
    delegation:
        support: none
    diff_mode:
        support: none
    platform:
        platforms: all
notes:
      - Starting in 2.2, if you specify 0 or negative for minutes or seconds, it will wait for 1 second, previously it would wait indefinitely.
      - User input is not captured or echoed, regardless of echo setting, when minutes or seconds is specified.
"""

EXAMPLES = """
- name: Pause for 5 minutes to build app cache
  ansible.builtin.pause:
    minutes: 5

- name: Pause until you can verify updates to an application were successful
  ansible.builtin.pause:

- name: A helpful reminder of what to look out for post-update
  ansible.builtin.pause:
    prompt: "Make sure org.foo.FooOverload exception is not present"

- name: Pause to get some sensitive input
  ansible.builtin.pause:
    prompt: "Enter a secret"
    echo: no
"""

RETURN = """
user_input:
  description: User input from interactive console
  returned: if no waiting time set
  type: str
  sample: Example user input
start:
  description: Time when started pausing
  returned: always
  type: str
  sample: "2017-02-23 14:35:07.298862"
stop:
  description: Time when ended pausing
  returned: always
  type: str
  sample: "2017-02-23 14:35:09.552594"
delta:
  description: Time paused in seconds
  returned: always
  type: str
  sample: 2
stdout:
  description: Output of pause module
  returned: always
  type: str
  sample: Paused for 0.04 minutes
echo:
  description: Value of echo setting
  returned: always
  type: bool
  sample: true
"""
