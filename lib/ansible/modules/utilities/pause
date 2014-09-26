# -*- mode: python -*-

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
      - Number of minutes to pause for.
    required: false
    default: null
  seconds:
    description:
      - Number of seconds to pause for.
    required: false
    default: null
  prompt:
    description:
      - Optional text to use for the prompt message.
    required: false
    default: null
author: Tim Bielawa
'''

EXAMPLES = '''
# Pause for 5 minutes to build app cache.
- pause: minutes=5

# Pause until you can verify updates to an application were successful.
- pause:

# A helpful reminder of what to look out for post-update.
- pause: prompt="Make sure org.foo.FooOverload exception is not present"
'''
