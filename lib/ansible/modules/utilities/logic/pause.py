# -*- mode: python -*-

# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: pause
short_description: Pause playbook execution
description:
  - Pauses playbook execution for a set amount of time, or until a prompt is acknowledged. All parameters are optional. The default behavior is to pause with a prompt.
  - "You can use C(ctrl+c) if you wish to advance a pause earlier than it is set to expire or if you need to abort a playbook run entirely. To continue early: press C(ctrl+c) and then C(c). To abort a playbook: press C(ctrl+c) and then C(a)."
  - "The pause module integrates into async/parallelized playbooks without any special considerations (see also: Rolling Updates). When using pauses with the C(serial) playbook parameter (as in rolling updates) you are only prompted once for the current group of hosts."
version_added: "0.8"
options:
  minutes:
    description:
      - A positive number of minutes to pause for.
    required: false
    default: null
  seconds:
    description:
      - A positive number of seconds to pause for.
    required: false
    default: null
  prompt:
    description:
      - Optional text to use for the prompt message.
    required: false
    default: null
author: "Tim Bielawa (@tbielawa)"
notes:
      - Starting in 2.2,  if you specify 0 or negative for minutes or seconds, it will wait for 1 second, previously it would wait indefinitely.
'''

EXAMPLES = '''
# Pause for 5 minutes to build app cache.
- pause:
    minutes: 5

# Pause until you can verify updates to an application were successful.
- pause:

# A helpful reminder of what to look out for post-update.
- pause:
    prompt: "Make sure org.foo.FooOverload exception is not present"
'''

RETURN = '''
user_input:
  description: User input from interactive console
  returned: if no waiting time set
  type: string
  sample: Example user input
start:
  description: Time when started pausing
  returned: always
  type: string
  sample: 2017-02-23 14:35:07.298862
stop:
  description: Time when ended pausing
  returned: always
  type: string
  sample: 2017-02-23 14:35:09.552594
delta:
  description: Time paused in seconds
  returned: always
  type: string
  sample: 2
stdout:
  description: Output of pause module
  returned: always
  type: string
  sample: Paused for 0.04 minutes
'''
