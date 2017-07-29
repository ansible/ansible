#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Michael DeHaan <michael@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: osx_say
version_added: "1.2"
short_description: Makes an OSX computer to speak.
description:
   - makes an OS computer speak!  Amuse your friends, annoy your coworkers!
notes:
   - If you like this module, you may also be interested in the osx_say callback in the plugins/ directory of the source checkout.
options:
  msg:
    description:
      What to say
    required: true
  voice:
    description:
      What voice to use
    required: false
requirements: [ say ]
author:
    - "Ansible Core Team"
    - "Michael DeHaan (@mpdehaan)"
'''

EXAMPLES = '''
- osx_say:
    msg: '{{ inventory_hostname }} is all done'
    voice: Zarvox
  delegate_to: localhost
'''
import os

from ansible.module_utils.basic import AnsibleModule


DEFAULT_VOICE='Alex'


def say(module, msg, voice):
    module.run_command(["/usr/bin/say", msg, "--voice=%s" % (voice)], check_rc=True)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            msg=dict(required=True),
            voice=dict(required=False, default=DEFAULT_VOICE),
        ),
        supports_check_mode=False
    )

    if not os.path.exists("/usr/bin/say"):
        module.fail_json(msg="/usr/bin/say is not installed")

    msg   = module.params['msg']
    voice = module.params['voice']

    say(module, msg, voice)

    module.exit_json(msg=msg, changed=False)


if __name__ == '__main__':
    main()
