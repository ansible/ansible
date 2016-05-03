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
author: "Christian Berendt (@berendt)"
short_description: enables/disables a module of the Apache2 webserver
description:
   - Enables or disables a specified module of the Apache2 webserver.
options:
   name:
     description:
        - name of the module to enable/disable
     required: true
   force:
     description:
        - force disabling of default modules and override Debian warnings
     required: false
     choices: ['yes', 'no']
     default: no
     version_added: "2.1"
   state:
     description:
        - indicate the desired state of the resource
     choices: ['present', 'absent']
     default: present

requirements: ["a2enmod","a2dismod"]
'''

EXAMPLES = '''
# enables the Apache2 module "wsgi"
- apache2_module: state=present name=wsgi

# disables the Apache2 module "wsgi"
- apache2_module: state=absent name=wsgi
'''

import re

def _run_threaded(module):
    control_binary = _get_ctl_binary(module)

    result, stdout, stderr = module.run_command("%s -V" % control_binary)

    if re.search(r'threaded:[ ]*yes', stdout):
        return True
    else:
        return False

def _get_ctl_binary(module):
    for command in ['apache2ctl', 'apachectl']:
        ctl_binary = module.get_bin_path(command)
        if ctl_binary is not None:
            return ctl_binary

    module.fail_json(
      msg="None of httpd, apachectl or apach2ctl found. At least one apache control binary is necessary.")

def _module_is_enabled(module):
    control_binary = _get_ctl_binary(module)
    name = module.params['name']

    result, stdout, stderr = module.run_command("%s -M" % control_binary)

    if result != 0:
        module.fail_json(msg="Error executing %s: %s" % (control_binary, stderr))

    if re.search(r' ' + name + r'_module', stdout):
        return True
    else:
        return False

def _set_state(module, state):
    name = module.params['name']
    force = module.params['force']

    want_enabled = state == 'present'
    state_string = {'present': 'enabled', 'absent': 'disabled'}[state]
    a2mod_binary = {'present': 'a2enmod', 'absent': 'a2dismod'}[state]
    success_msg = "Module %s %s" % (name, state_string)

    if _module_is_enabled(module) != want_enabled:
        if module.check_mode:
            module.exit_json(changed = True, result = success_msg)

        a2mod_binary = module.get_bin_path(a2mod_binary)
        if a2mod_binary is None:
            module.fail_json(msg="%s not found. Perhaps this system does not use %s to manage apache" % (a2mod_binary, a2mod_binary))

        if not want_enabled and force:
            # force exists only for a2dismod on debian
            a2mod_binary += ' -f'

        result, stdout, stderr = module.run_command("%s %s" % (a2mod_binary, name))

        if _module_is_enabled(module) == want_enabled:
            module.exit_json(changed = True, result = success_msg)
        else:
            module.fail_json(msg="Failed to set module %s to %s: %s" % (name, state_string, stdout), rc=result, stdout=stdout, stderr=stderr)
    else:
        module.exit_json(changed = False, result = success_msg)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name  = dict(required=True),
            force = dict(required=False, type='bool', default=False),
            state = dict(default='present', choices=['absent', 'present'])
        ),
        supports_check_mode = True,
    )

    name = module.params['name']
    if name == 'cgi' and _run_threaded(module):
        module.fail_json(msg="Your MPM seems to be threaded. No automatic actions on module %s possible." % name)

    if module.params['state'] in ['present', 'absent']:
        _set_state(module, module.params['state'])

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
