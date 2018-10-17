#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2013-2014, Christian Berendt <berendt@b1-systems.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: apache2_module
version_added: 1.6
author:
    - Christian Berendt (@berendt)
    - Ralf Hertel (@n0trax)
    - Robin Roth (@robinro)
short_description: Enables/disables a module of the Apache2 webserver.
description:
   - Enables or disables a specified module of the Apache2 webserver.
options:
   name:
     description:
        - Name of the module to enable/disable as given to C(a2enmod/a2dismod).
     required: true
   identifier:
     description:
         - Identifier of the module as listed by C(apache2ctl -M).
           This is optional and usually determined automatically by the common convention of
           appending C(_module) to I(name) as well as custom exception for popular modules.
     required: False
     version_added: "2.5"
   force:
     description:
        - Force disabling of default modules and override Debian warnings.
     required: false
     type: bool
     default: False
     version_added: "2.1"
   state:
     description:
        - Desired state of the module.
     choices: ['present', 'absent']
     default: present
   ignore_configcheck:
     description:
        - Ignore configuration checks about inconsistent module configuration. Especially for mpm_* modules.
     type: bool
     default: False
     version_added: "2.3"
requirements: ["a2enmod","a2dismod"]
'''

EXAMPLES = '''
# enables the Apache2 module "wsgi"
- apache2_module:
    state: present
    name: wsgi
# disables the Apache2 module "wsgi"
- apache2_module:
    state: absent
    name: wsgi
# disable default modules for Debian
- apache2_module:
    state: absent
    name: autoindex
    force: True
# disable mpm_worker and ignore warnings about missing mpm module
- apache2_module:
    state: absent
    name: mpm_worker
    ignore_configcheck: True
# enable dump_io module, which is identified as dumpio_module inside apache2
- apache2_module:
    state: present
    name: dump_io
    identifier: dumpio_module
'''

RETURN = '''
result:
    description: message about action taken
    returned: always
    type: string
warnings:
    description: list of warning messages
    returned: when needed
    type: list
rc:
    description: return code of underlying command
    returned: failed
    type: int
stdout:
    description: stdout of underlying command
    returned: failed
    type: string
stderr:
    description: stderr of underlying command
    returned: failed
    type: string
'''

import re


def _run_threaded(module):
    control_binary = _get_ctl_binary(module)

    result, stdout, stderr = module.run_command("%s -V" % control_binary)

    return bool(re.search(r'threaded:[ ]*yes', stdout))


def _get_ctl_binary(module):
    for command in ['apache2ctl', 'apachectl']:
        ctl_binary = module.get_bin_path(command)
        if ctl_binary is not None:
            return ctl_binary

    module.fail_json(
        msg="Neither of apache2ctl nor apachctl found."
            " At least one apache control binary is necessary."
    )


def _module_is_enabled(module):
    control_binary = _get_ctl_binary(module)
    result, stdout, stderr = module.run_command("%s -M" % control_binary)

    if result != 0:
        error_msg = "Error executing %s: %s" % (control_binary, stderr)
        if module.params['ignore_configcheck']:
            if 'AH00534' in stderr and 'mpm_' in module.params['name']:
                module.warnings.append(
                    "No MPM module loaded! apache2 reload AND other module actions"
                    " will fail if no MPM module is loaded immediately."
                )
            else:
                module.warnings.append(error_msg)
            return False
        else:
            module.fail_json(msg=error_msg)

    searchstring = ' ' + module.params['identifier']
    return searchstring in stdout


def create_apache_identifier(name):
    """
    By convention if a module is loaded via name, it appears in apache2ctl -M as
    name_module.

    Some modules don't follow this convention and we use replacements for those."""

    # a2enmod name replacement to apache2ctl -M names
    text_workarounds = [
        ('shib2', 'mod_shib'),
        ('evasive', 'evasive20_module'),
    ]

    # re expressions to extract subparts of names
    re_workarounds = [
        ('php', r'^(php\d)\.'),
    ]

    for a2enmod_spelling, module_name in text_workarounds:
        if a2enmod_spelling in name:
            return module_name

    for search, reexpr in re_workarounds:
        if search in name:
            try:
                rematch = re.search(reexpr, name)
                return rematch.group(1) + '_module'
            except AttributeError:
                pass

    return name + '_module'


def _set_state(module, state):
    name = module.params['name']
    force = module.params['force']

    want_enabled = state == 'present'
    state_string = {'present': 'enabled', 'absent': 'disabled'}[state]
    a2mod_binary = {'present': 'a2enmod', 'absent': 'a2dismod'}[state]
    success_msg = "Module %s %s" % (name, state_string)

    if _module_is_enabled(module) != want_enabled:
        if module.check_mode:
            module.exit_json(changed=True,
                             result=success_msg,
                             warnings=module.warnings)

        a2mod_binary = module.get_bin_path(a2mod_binary)
        if a2mod_binary is None:
            module.fail_json(msg="%s not found. Perhaps this system does not use %s to manage apache" % (a2mod_binary, a2mod_binary))

        if not want_enabled and force:
            # force exists only for a2dismod on debian
            a2mod_binary += ' -f'

        result, stdout, stderr = module.run_command("%s %s" % (a2mod_binary, name))

        if _module_is_enabled(module) == want_enabled:
            module.exit_json(changed=True,
                             result=success_msg,
                             warnings=module.warnings)
        else:
            msg = (
                'Failed to set module {name} to {state}:\n'
                '{stdout}\n'
                'Maybe the module identifier ({identifier}) was guessed incorrectly.'
                'Consider setting the "identifier" option.'
            ).format(
                name=name,
                state=state_string,
                stdout=stdout,
                identifier=module.params['identifier']
            )
            module.fail_json(msg=msg,
                             rc=result,
                             stdout=stdout,
                             stderr=stderr)
    else:
        module.exit_json(changed=False,
                         result=success_msg,
                         warnings=module.warnings)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            identifier=dict(required=False, type='str'),
            force=dict(required=False, type='bool', default=False),
            state=dict(default='present', choices=['absent', 'present']),
            ignore_configcheck=dict(required=False, type='bool', default=False),
        ),
        supports_check_mode=True,
    )

    module.warnings = []

    name = module.params['name']
    if name == 'cgi' and _run_threaded(module):
        module.fail_json(msg="Your MPM seems to be threaded. No automatic actions on module %s possible." % name)

    if not module.params['identifier']:
        module.params['identifier'] = create_apache_identifier(module.params['name'])

    if module.params['state'] in ['present', 'absent']:
        _set_state(module, module.params['state'])

# import module snippets
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
