#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Björn Albers <bjoernalbers@gmail.com>
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
module: osx_service
author: "Björn Albers <bjoernalbers@gmail.com>"
version_added: "2.2"
short_description: Manage Mac OS X system services via launchctl
description:
  - Start, stop and restart Mac OS X system services that have a valid launchd
    plist under /Library/LaunchDaemons.
options:
  name:
    description:
      Label of job
    required: true
  state:
    description:
      Desired state
    required: true
    choices: [ "started", "stopped", "restarted" ]
requirements: [ launchctl ]
'''

EXAMPLES = '''
- osx_service: name=com.docker.vmnetd state=started
'''


class OSXService:
    COMMAND   = '/bin/launchctl'
    PLIST_DIR = '/Library/LaunchDaemons'

    def __init__(self, module):
        self.module = module
        self.name   = module.params['name']

    def start(self):
        if not self.__started():
            return self.__launchctl(['load', '-w', self.__plist()])
        else:
            return False

    def stop(self):
        if self.__started():
            return self.__launchctl(['unload', '-w', self.__plist()])
        else:
            return False

    def restart(self):
        self.stop()
        return self.start()

    def __started(self):
        (rc, _, _) = self.module.run_command(
            [self.COMMAND, 'list', self.name])
        return rc == 0

    def __plist(self):
        return os.path.join(self.PLIST_DIR, self.name + '.plist')

    def __launchctl(self, arguments):
          (_, _, stderr) = self.module.run_command(
              [self.COMMAND] + arguments, check_rc=True)
          if stderr:
              self.module.fail_json(msg=stderr)
          else:
              return True
        

def main():

    module = AnsibleModule(
        argument_spec = dict(
            name  = dict(required = True),
            state = dict(required = True,
                choices = ['started', 'stopped', 'restarted']),
        ),
        supports_check_mode = False
    )

    if os.geteuid() != 0:
        module.fail_json(msg='Please run as root!')

    name  = module.params['name']
    state = module.params['state']

    service = OSXService(module)
    if state == 'started':
        changed = service.start()
    elif state == 'stopped':
        changed = service.stop()
    elif state == 'restarted':
        changed = service.restart()

    module.exit_json(name=name, state=state, changed=changed) 


# import module snippets
from ansible.module_utils.basic import *
main()
