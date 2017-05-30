#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Jasper Lievisse Adriaanse <j@jasper.la>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: smartos_timezone
short_description: Manage timezone in SmartOS instances/zones
description:
    - Manage the timezone in a SmartOS instance/zone. Adjusting the
      timezone for the Global Zone is not supported.
version_added: "2.3"
author: Jasper Lievisse Adriaanse (@jasperla)
options:
    timezone:
        required: false
        aliases: [ "name" ]
        description:
        - Name of the timezone.
'''

EXAMPLES = '''
- name: Set timezone to Europe/Amsterdam
  smartos_timezone:
    name: Europe/Amsterdam
'''

import os
import re

def get_timezone(module):
    try:
        f = open('/etc/default/init', 'r')
        for line in f:
            m = re.match('^TZ=(.*)$', line.strip())
            if m:
                return m.groups()[0]
    except:
        module.fail_json(msg='Failed to read /etc/default/init')

def set_timezone(module):
    tz = module.params['timezone']
    cmd = 'sm-set-timezone {0}'.format(tz)

    (rc, stdout, stderr) = module.run_command(cmd)

    if rc != 0:
        module.fail_json(msg=stderr)

    # sm-set-timezone knows no state and will always set the timezone.
    # XXX: Wording bug in sm-set-timezone
    m = re.match('^\* Changed (to)? timezone (to)? ({0}).*'.format(tz), stdout.splitlines()[1])
    if m and m.groups()[-1] == tz:
        return True
    else:
        return False

def main():
    module = AnsibleModule(
        argument_spec=dict(
            timezone=dict(default=None, aliases=['name'])
        ),
        supports_check_mode=True
    )

    timezone = module.params['timezone']

    result = { 'timezone': timezone }
    changed = False

    # First get our current timezone to see if anything needs to be done.
    if get_timezone(module) != timezone:
        changed = True

    # Unless we're in check mode or if there will be no change that's all
    # that was needed.
    if not module.check_mode and changed:
        if set_timezone(module):
            changed = True

    result['changed'] = changed
    module.exit_json(**result)

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
