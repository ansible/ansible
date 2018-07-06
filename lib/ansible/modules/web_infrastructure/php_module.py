#!/usr/bin/python
#coding: utf-8 -*-

# (c) 2016, Wong Hoi Sing Edison <hswong3i@pantarei-design.com>
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
module: php_module
version_added: 2.4
author: "Wong Hoi Sing Edison (@hswong3i)"
short_description: enables/disables a module of the PHP
description:
   - Enables or disables a specified module of the PHP.
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
   version:
     description:
        - indicate the version of php for enable/disable
     default: ALL
   sapi:
     description:
        - indicate the sapi of php for enable/disable
     default: ALL

requirements: ["phpenmod","phpdismod"]
'''

EXAMPLES = '''
# enables the PHP module "gd"
- php_module: state=present name=gd

# disables the PHP module "gd"
- php_module: state=absent name=gd

# enables the php module "gd" for php 7.0 only
- php_module: state=present name=gd version=7.0

# enables the php module "gd" for php fpm only
- php_module: state=present name=gd sapi=fpm
'''

RETURN = '''
'''

import re

def _check_module(module):
    name = module.params['name']

    result, stdout, stderr = module.run_command("%s -m %s" % (module.get_bin_path('phpenmod'), name))
    
    if re.search(r'Not enabling the ' + name + r' module', stderr):
        return 'absent'
    else:
        return 'present'

def _enable_module(module):
    name = module.params['name']
    state = module.params['state']
    version = module.params['version']
    sapi = module.params['sapi']
    
    current_state = _check_module(module)

    result, stdout, stderr = module.run_command("%s -v %s -s %s %s" % (module.get_bin_path('phpenmod'), version, sapi, name))
    
    if result != 0:
        module.fail_json(msg = "Failed to enable %s: %s" % (name, stdout))
    else:
        module.exit_json(changed = (current_state != state), result = "%s %s" % (name, state))

def _disable_module(module):
    name = module.params['name']
    state = module.params['state']
    version = module.params['version']
    sapi = module.params['sapi']
    
    current_state = _check_module(module)
    
    result, stdout, stderr = module.run_command("%s -v %s -s %s %s" % (module.get_bin_path('phpdismod'), version, sapi, name))
    
    if result != 0:
        module.fail_json(msg = "Failed to disable %s: %s" % (name, stdout))
    else:
        module.exit_json(changed = (current_state != state), result = "%s %s" % (name, state))

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name  = dict(required = True),
            state = dict(default = 'present', choices = ['absent', 'present']),
            version = dict(required = False, default = 'ALL'),
            sapi = dict(required = False, default = 'ALL'),
        ),
        supports_check_mode = True,
    )

    for binary in ['phpenmod', 'phpdismod']:
        bin_path = module.get_bin_path(binary)
        if bin_path is None:
            module.fail_json(msg = "%s not found" % binary)

    if module.check_mode:
        module.exit_json(changed = (_check_module(module) != module.params['state']))

    if module.params['state'] == 'present':
        _enable_module(module)
    
    if module.params['state'] == 'absent':
        _disable_module(module)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
