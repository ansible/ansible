#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Bianca Henderson <beeankha@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '2.6',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tutorial
short_description: Rolls a D20, yo.
description:
     - This thing rolls a D20.
       If you roll a 1, it taunts you and tells you that you got a crit fail.
       If you roll a 20, it congratulates you by telling you that you got a nat twenty.
version_added: "2.6"
options: {}
notes: []
requirements: [ "DnD" ]
author:
    - "Getting Started Team"
    - "Bianca Henderson (@beeankha)"
'''

EXAMPLES = '''
# Rolls a D20, hopes to pass the bug test filter thing.
'''
from random import randint
from ansible.module_utils.basic import AnsibleModule

import sys
import os
import json

print('Input any key to roll!')
do_roll = input()

roll = (randint(1,20))
if roll == 1:
    print(f"You rolled a {roll}, CRITICAL MISS!")
elif roll == 20:
    print("You rolled a NATURAL TWENTY!")
else:
    print(f"Your roll is {roll}.")

os.execl(sys.executable, sys.executable, *sys.argv)


def main():
    module = AnsibleModule(
        argument_spec=dict()
    )
    cmd = ["/usr/bin/env"]
    rc, out, err = module.run_command(cmd, check_rc=True)
    module.exit_json(**json.loads(out))


if __name__ == '__main__':
    main()
print("hello world")
