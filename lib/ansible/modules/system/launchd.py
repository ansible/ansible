#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, Brian Coca <bcoca@ansible.com>
# (c) 2106, Theo Crevon (https://github.com/tcr-ableton)
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
module: launchd
author:
    - 'Ansible Core Team'
    - 'Theo Crevon (@tcr-ableton)'
    - 'Björn Albers <bjoernalbers@gmail.com>'
version_added: '2.2'
short_description: Manage Mac OS X launchd services.
description:
    - Manage (start, stop and restart) Mac OS X launchd services via launchctl.
options:
    name:
        required: true
        description:
            - Name of the service.
        aliases: [ 'service', 'label' ]
    state:
        required: true
        choices: [ 'started', 'loaded', 'stopped', 'unloaded', 'restarted', 'reloaded' ]
        description:
            - C(started), C(loaded), C(stopped) and C(unloaded) are idempotent
              actions that will not run commands unless necessary.
              Launchd does not support C(restarted) / C(reloaded) natively, so
              these will both trigger a stop and start as needed.
requirements:
    - target host OS must be Mac OS X
    - you have to run the module as root via sudo
    - the service must be a system service and have a valid launchd plist under
      /Library/LaunchDaemons
'''

RETURN = '''
# These values will be returned on success...
name:
    description: Name of the service.
    type: string
    sample: 'com.docker.vmnetd'
state:
    description: Current state of the service.
    type: string
    sample: 'started'
changed:
    description: Did the service state change?
    type: boolean
    sample: True
'''

EXAMPLES = '''
- name: ensure com.docker.vmnetd is started
  launchd:
      name: com.docker.vmnetd
      state: started
      become: yes
      become_user: root
'''


import os

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
            name = dict(
                required = True,
                type     = 'str',
                aliases  = [ 'service', 'label' ]
            ),
            state = dict(
                required = True,
                type     = 'str',
                choices  = [ 'started',   'loaded',
                             'stopped',   'unloaded',
                             'restarted', 'reloaded' ]
            ),
        ),
        supports_check_mode = False
    )

    if os.geteuid() != 0:
        module.fail_json(msg='Please run as root!')

    name  = module.params['name']
    state = module.params['state']

    service = OSXService(module)
    if state in [ 'started', 'loaded' ] :
        changed = service.start()
    elif state in [ 'stopped', 'unloaded' ]:
        changed = service.stop()
    elif state in [ 'restarted', 'reloaded' ]:
        changed = service.restart()

    module.exit_json(name=name, state=state, changed=changed) 


# import module snippets
from ansible.module_utils.basic import *
main()
