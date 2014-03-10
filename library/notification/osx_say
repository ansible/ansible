#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Michael DeHaan <michael@ansible.com>
#
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
author: Michael DeHaan
'''

EXAMPLES = '''
- local_action: osx_say msg="{{inventory_hostname}} is all done" voice=Zarvox
'''

DEFAULT_VOICE='Trinoids'

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

# import module snippets
from ansible.module_utils.basic import *
main()
