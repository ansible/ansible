#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2013-2014, Christian Berendt <berendt@b1-systems.de>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: apache2_module
version_added: 1.6
short_description: enables/disables a module of the Apache2 webserver
description:
   - Enables or disables a specified module of the Apache2 webserver.
options:
   name:
     description:
        - name of the module to enable/disable
     required: true
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present

'''

EXAMPLES = '''
# enables the Apache2 module "wsgi"
- apache2_module: state=present name=wsgi

# disables the Apache2 module "wsgi"
- apache2_module: state=absent name=wsgi
'''

import re

def _disable_module(module):
    name = module.params['name']
    a2dismod_binary = module.get_bin_path("a2dismod")
    if a2dismod_binary is None:
        module.fail_json(msg="a2dismod not found.  Perhaps this system does not use a2dismod to manage apache")

    result, stdout, stderr = module.run_command("%s %s" % (a2dismod_binary, name))

    if re.match(r'.*\b' + name + r' already disabled', stdout, re.S):
        module.exit_json(changed = False, result = "Success")
    elif result != 0:
        module.fail_json(msg="Failed to disable module %s: %s" % (name, stdout))
    else:
        module.exit_json(changed = True, result = "Disabled")

def _enable_module(module):
    name = module.params['name']
    a2enmod_binary = module.get_bin_path("a2enmod")
    if a2enmod_binary is None:
        module.fail_json(msg="a2enmod not found.  Perhaps this system does not use a2enmod to manage apache")

    result, stdout, stderr = module.run_command("%s %s" % (a2enmod_binary, name))

    if re.match(r'.*\b' + name + r' already enabled', stdout, re.S):
        module.exit_json(changed = False, result = "Success")
    elif result != 0:
        module.fail_json(msg="Failed to enable module %s: %s" % (name, stdout))
    else:
        module.exit_json(changed = True, result = "Enabled")

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name  = dict(required=True),
            state = dict(default='present', choices=['absent', 'present'])
        ),
    )

    if module.params['state'] == 'present':
        _enable_module(module)

    if module.params['state'] == 'absent':
        _disable_module(module)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
